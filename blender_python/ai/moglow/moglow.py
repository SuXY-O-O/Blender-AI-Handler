import torch
import numpy as np
from sklearn.preprocessing import StandardScaler
from .builder import build
from .config import JsonConfig
from ai_interface import AiInterface
from scipy.spatial.transform import Rotation


def mirror_data(data):
    aa = data.copy()
    aa[:, :, 3:15] = data[:, :, 15:27]
    aa[:, :, 3:15:3] = -data[:, :, 15:27:3]
    aa[:, :, 15:27] = data[:, :, 3:15]
    aa[:, :, 15:27:3] = -data[:, :, 3:15:3]
    aa[:, :, 39:51] = data[:, :, 51:63]
    aa[:, :, 39:51:3] = -data[:, :, 51:63:3]
    aa[:, :, 51:63] = data[:, :, 39:51]
    aa[:, :, 51:63:3] = -data[:, :, 39:51:3]
    aa[:, :, 63] = -data[:, :, 63]
    aa[:, :, 65] = -data[:, :, 65]
    return aa


def reverse_time(data):
    aa = data[:, -1::-1, :].copy()
    aa[:, :, 63] = -aa[:, :, 63]
    aa[:, :, 64] = -aa[:, :, 64]
    aa[:, :, 65] = -aa[:, :, 65]
    return aa


def inv_standardize(data, scaler):
    shape = data.shape
    flat = data.reshape((shape[0] * shape[1], shape[2]))
    scaled = scaler.inverse_transform(flat).reshape(shape)
    return scaled


def fit_and_standardize(data) -> StandardScaler:
    shape = data.shape
    flat = data.copy().reshape((shape[0] * shape[1], shape[2]))
    scaler = StandardScaler().fit(flat)
    # scaled = scaler.transform(flat).reshape(shape)
    return scaler


def standardize(data, scaler):
    shape = data.shape
    flat = data.copy().reshape((shape[0] * shape[1], shape[2]))
    scaled = scaler.transform(flat).reshape(shape)
    return scaled


class MoGlow(AiInterface):
    def __init__(self):
        self.graph = None
        self.pos_data = None
        self.ctr_data = None
        self.device = None
        self.scaler = None
        hparams = JsonConfig("/home/suxy/Documents/BiYeSheJi/blender_file/blender_python/ai/moglow/args"
                             "/locomotion.json")
        x_channels = 63
        cond_channels = 66 * hparams.Data.seqlen + 3
        # build graph
        print("Building graph...")
        self.graph = build(x_channels, cond_channels, hparams, False)
        self.graph.eval()
        # init datas
        print("Load graph data...")
        self.device = torch.device(hparams.Device.data)
        self.pos_data = torch.zeros([1, x_channels * hparams.Data.seqlen, 1]).to(self.device)
        self.ctr_data = torch.zeros([1, 3 * hparams.Data.seqlen, 1]).to(self.device)
        # init scaler
        print("Reload train data and calculate scale...")
        train_series = np.load("/home/suxy/Documents/BiYeSheJi/AI/StyleGestures-master/data/locomotion"
                               "/all_locomotion_train_20fps.npz")
        train_data = train_series['clips'].astype(np.float32)
        del train_series
        train_data = train_data[:-100, :, :]
        if hparams.Data.mirror:
            print("Mirroring...")
            mirrored = mirror_data(train_data)
            train_data = np.concatenate((train_data, mirrored), axis=0)
        if hparams.Data.reverse_time:
            print("Reversing...")
            rev = reverse_time(train_data)
            train_data = np.concatenate((train_data, rev), axis=0)
        self.scaler = fit_and_standardize(train_data)
        del train_data
        print("End Building, begin modal.")
        # make the model move
        self.rot = Rotation.from_euler("Z", 0)
        self.pos = np.array([0., 0., 0.])
        return

    def end(self) -> bool:
        del self.graph
        del self.pos_data
        del self.ctr_data
        self.ctr_data = None
        self.pos_data = None
        self.graph = None
        torch.cuda.empty_cache()
        return True

    def get_next(self, control_arg: list):
        # generate input data
        control = torch.tensor(control_arg).reshape(1, -1, 1).to(self.device)
        input_data = torch.cat([
            self.pos_data,
            self.ctr_data,
            control
        ], dim=1)
        # forward
        output_data = self.graph(z=None, cond=input_data, eps_std=1, reverse=True)
        # update data
        self.pos_data = torch.cat([
            self.pos_data[:, 63:, :],
            output_data
        ], dim=1)
        self.ctr_data = torch.cat([
            self.ctr_data[:, 3:, :],
            control
        ], dim=1)
        # output data
        output_data = output_data.cpu().numpy()
        output_data = np.concatenate([output_data.reshape(-1), control_arg])
        output_data = inv_standardize(output_data.reshape([1, 1, -1]), self.scaler)
        # calculate movement
        output_data = output_data.reshape(-1, 3)
        x = output_data[-1, -3]
        z = output_data[-1, -2]
        r = -output_data[-1, -1]
        y = output_data[0, 1]
        output_data = output_data[:-1]
        output_data -= output_data[0]
        this_rot = Rotation.from_euler("y", r)
        this_pos = np.array([x, 0., z])
        this_pos = self.rot.apply(this_pos)
        output_data = self.rot.apply(output_data)
        output_data += self.pos
        output_data += np.array([0., y, 0.])
        self.rot *= this_rot
        self.pos += this_pos
        print([z, x, self.rot.as_euler('YXZ')[0]])
        return {
            "data": output_data.reshape(-1),
            "control": [z, x, self.rot.as_euler('YXZ')[0]]
        }
