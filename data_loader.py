from torch.utils.data import Dataset
import parameter
import numpy as np
import os
import feature_class
import random
import torch
import data_augmentation as aug

''' data output format: 
    mel: n_samples x channels x frame sequence length x n_mel (4000 x 7 x 300 x 64)
    raw: n_samples x channels x samples (4000 x 4 x 144000)
    label output format: n_samples x label_sequence_length x 3*classes (4000 x 60 x 42)
'''


class Tau_Nigens(Dataset):
    def __init__(self, parameters, split, shuffle=True, is_eval=False, is_val=False, is_aug=0):
        self.params = parameters
        self._input = self.params.input
        self._is_eval = is_eval
        self.is_val = is_val
        self._splits = np.array(split)
        self._feature_seq_len = self.params.feature_sequence_length
        self._label_seq_len = self.params.label_sequence_length
        self._shuffle = shuffle
        self._feat_cls = feature_class.FeatureClass(params=self.params, is_eval=self._is_eval)
        self._label_dir = self._feat_cls.get_label_dir()
        self._feat_dir = self._feat_cls.get_normalized_feat_dir()
        self._foa_dir = self._feat_cls.get_raw_dir()
        self._augmentation = is_aug

        self.data_size = 6
        self._nb_mel_bins = self._feat_cls.get_nb_mel_bins()
        self._nb_classes = self._feat_cls.get_nb_classes()

        self._filenames_list = list()
        self._nb_frames_file = 0
        self._nb_ch = None
        self._get_filenames_list_and_feat_label_sizes()  # update above parameters

        if self._shuffle:
            random.shuffle(self._filenames_list)

        self._len_file = len(self._filenames_list)

        # get data and label
        if self._input == "mel":
            self.data = self.get_all_data_mel()
        elif self._input == "raw":
            self.data = self.get_all_data_raw()
        self.label = self.get_all_label()

        # if self._input == "mel" and self._augmentation == 1:
        #     self.spec_augmentation()

        if self.params.quick_test == 1:
            self.data = self.data[:500]
            self.label = self.label[:500]

        print(
            '\tfiles number: {}, classes number:{}\n'
            '\tnumber of frames per file: {}, mel bins length: {}, channels number: {}\n'
            '\tfeat length per sequence: {}, label length per sequence: {}\n'.format(
                len(self._filenames_list),  self._nb_classes,
                self._nb_frames_file, self._nb_mel_bins, self._nb_ch,
                self._feature_seq_len, self._label_seq_len))

    def get_all_data_mel(self):
        print("\tstart to fetch mel spectrogram features data")
        data = []
        for file in self._filenames_list:
            features_per_file = np.load(os.path.join(self._feat_dir, file))  # 3000*448 (448 is mel * channel)
            sequence_length = int(len(features_per_file) // 10)
            interval = sequence_length if self.is_val else int(sequence_length/self.data_size)
            iteration = int((3000 - sequence_length) / interval + 1)
            for i in range(iteration):
                data_seg = features_per_file[i*interval:i*interval+sequence_length]
                data.append(data_seg)

        data = np.array(data)
        data = np.reshape(data, (-1, self._feature_seq_len, self._nb_mel_bins, self._nb_ch))
        data = np.transpose(data, (0, 3, 1, 2))  # samples, channel, width, height
        print("\tData frames shape: [n_samples, channel, width, height]:{}\n".format(data.shape))
        return torch.tensor(data, dtype=torch.float)

    def get_all_data_raw(self):
        print("\tstart to get fetch raw audio data")
        data = []
        sequence_length = 144000
        interval = sequence_length if self.is_val else int(sequence_length/self.data_size)
        iteration = int((1440000 - sequence_length) / interval + 1)
        for file in self._filenames_list:
            foa_path = os.path.join(self._foa_dir, file)
            mic_path = os.path.join("../Datasets/SELD2020/mic_dev", file)
            foa, fs = self._feat_cls.load_audio(foa_path)
            mic, fs = self._feat_cls.load_audio(mic_path)
            for i in range(iteration):
                foa_seg = foa[i * interval: i * interval + sequence_length].numpy().T
                mic_seg = mic[i * interval: i * interval + sequence_length].numpy().T
                data_seg = np.concatenate([mic_seg, foa_seg], axis=0)
                data.append(data_seg)

        data = np.array(data)
        print("\tData frames shape: [n_samples, channel, audio_samples]:{}\n".format(data.shape))
        return torch.tensor(data, dtype=torch.float)

    def get_all_label(self):
        label = []
        # if is validation or test, do not contain overlap data
        sequence_length = 60
        interval = sequence_length if self.is_val else int(sequence_length/self.data_size)
        iteration = int((600 - sequence_length) / interval + 1)
        for file in self._filenames_list:
            if self._input == "raw":
                file = file.split('.')[0] + ".npy"
            temp_label = np.load(os.path.join(self._label_dir, file))
            for i in range(iteration):
                label_seg = temp_label[i * interval: i * interval + sequence_length]
                label.append(label_seg)

        label = np.array(label)

        # accdoa
        mask = label[:, :, :self._nb_classes]
        mask = np.tile(mask, 3)
        label = mask * label[:, :, self._nb_classes:]

        print("\tLabel shape:{}\n".format(label.shape))

        return torch.tensor(label, dtype=torch.float)

    def spec_augmentation(self):
        print("start mel-spectrogram spec-augmentation")
        for i, data in enumerate(self.data):
            aug_freq_data = aug.freq_mask(data).unsqueeze(0)
            self.data = torch.cat((self.data, aug_freq_data), 0)
            self.label = torch.cat((self.label, self.label[i].unsqueeze(0)), 0)
            aug_time_data = aug.time_mask(data).unsqueeze(0)
            self.data = torch.cat((self.data, aug_time_data), 0)
            self.label = torch.cat((self.label, self.label[i].unsqueeze(0)), 0)

    def __getitem__(self, index):
        entry = {"feature": self.data[index], "label": self.label[index]}
        return entry

    def __len__(self):
        return len(self.data)

    def _get_filenames_list_and_feat_label_sizes(self):
        if self._input == "mel":
            for filename in os.listdir(self._feat_dir):
                if self._is_eval:
                    self._filenames_list.append(filename)
                else:
                    if int(filename[4]) in self._splits:  # check which split the file belongs to
                        self._filenames_list.append(filename)
            temp_feat = np.load(os.path.join(self._feat_dir, self._filenames_list[0]))
            self._nb_frames_file = temp_feat.shape[0]
            self._nb_ch = temp_feat.shape[1] // self._nb_mel_bins

        elif self._input == "raw":
            self._nb_ch = 4
            for filename in os.listdir(self._foa_dir):
                if self._is_eval:
                    self._filenames_list.append(filename)
                else:
                    if int(filename[4]) in self._splits:  # check which split the file belongs to
                        self._filenames_list.append(filename)

    def get_nb_classes(self):
        return self._nb_classes

    def nb_frames_1s(self):
        return self._feat_cls.nb_frames_1s()

    def get_filelist(self):
        return self._filenames_list


if __name__ == "__main__":
    params = parameter.get_params()
    dataset = Tau_Nigens(params, split=[3, 4, 5, 6])
