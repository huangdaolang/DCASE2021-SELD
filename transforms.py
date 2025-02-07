import random
import torch
import feature_class
import numpy as np
import data_augmentation
import parameter


class Swap_Channel(object):
    def __init__(self):
        self.p = None

    def __call__(self, data, label, p):
        x = label[:, :, :12]
        y = label[:, :, 12:24]
        z = label[:, :, 24:]
        new_label = None
        new_data = None
        if 0 <= p < 0.125:
            new_data = data
            new_label = label
        if 0.125 <= p < 0.250:
            new_data = torch.stack((data[:, 1], data[:, 3], data[:, 0], data[:, 2],
                                data[:, 4], -data[:, 7], -data[:, 6], data[:, 5]), dim=1)
            new_x = y
            new_y = -x
            new_z = -z
            new_label = torch.cat([new_x, new_y, new_z], dim=2)
        elif 0.250 <= p < 0.375:
            new_data = torch.stack((data[:, 3], data[:, 1], data[:, 2], data[:, 0],
                                data[:, 4], -data[:, 7], data[:, 6], -data[:, 5]), dim=1)
            new_x = -y
            new_y = -x
            new_z = z
            new_label = torch.cat([new_x, new_y, new_z], dim=2)
        elif 0.375 <= p < 0.500:
            new_data = torch.stack((data[:, 1], data[:, 0], data[:, 3], data[:, 2],
                                data[:, 4], -data[:, 5], -data[:, 6], data[:, 7]), dim=1)
            new_x = x
            new_y = -y
            new_z = -z
            new_label = torch.cat([new_x, new_y, new_z], dim=2)
        elif 0.500 <= p < 0.625:
            new_data = torch.stack((data[:, 2], data[:, 0], data[:, 3], data[:, 1],
                                data[:, 4], data[:, 7], -data[:, 6], -data[:, 5]), dim=1)
            new_x = -y
            new_y = x
            new_z = -z
            new_label = torch.cat([new_x, new_y, new_z], dim=2)
        elif 0.625 <= p < 0.750:
            new_data = torch.stack((data[:, 0], data[:, 2], data[:, 1], data[:, 3],
                                data[:, 4], data[:, 7], data[:, 6], data[:, 5]), dim=1)
            new_x = y
            new_y = x
            new_z = z
            new_label = torch.cat([new_x, new_y, new_z], dim=2)
        elif 0.750 <= p < 0.875:
            new_data = torch.stack((data[:, 3], data[:, 2], data[:, 1], data[:, 0],
                                data[:, 4], -data[:, 5], data[:, 6], -data[:, 7]), dim=1)
            new_x = -x
            new_y = -y
            new_z = z
            new_label = torch.cat([new_x, new_y, new_z], dim=2)
        elif 0.875 <= p < 1:
            new_data = torch.stack((data[:, 2], data[:, 3], data[:, 0], data[:, 1],
                                data[:, 4], data[:, 5], -data[:, 6], -data[:, 7]), dim=1)
            new_x = -x
            new_y = y
            new_z = -z
            new_label = torch.cat([new_x, new_y, new_z], dim=2)
        return new_data.to(data.device), new_label.to(label.device)


if __name__ == "__main__":
    data = torch.tensor([
        [[0, 0, 1], [1, 1, 2], [2, 2, 3], [3, 3, 4], [4, 4, 5], [5, 5, 6], [6, 6, 7], [7, 7, 8]],
        [[1, 1, 1], [2, 2, 1], [3, 3, 1], [30, 30, 1], [4, 4, 1], [5, 5, 1], [6, 6, 1], [7, 7, 1]],
        [[0, 0, 1], [1, 1, 1], [2, 2, 1], [3, 3, 1], [4, 4, 1], [5, 5, 1], [6, 6, 1], [7, 7, 1]]
    ])

    swap_channel = Swap_Channel()
    tmp_label_1 = np.load("../Datasets/SELD2020/feat_label/foa_dev_label/fold1_room1_mix010_ov1.npy")[:10, 12:]
    tmp_label_2 = np.load("../Datasets/SELD2020/feat_label/foa_dev_label/fold1_room1_mix012_ov1.npy")[184:194, 12:]
    tmp_label = np.stack([tmp_label_1, tmp_label_2], axis=0)

    data, label = swap_channel(data, torch.tensor(tmp_label), 0.3)

