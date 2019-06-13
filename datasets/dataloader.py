# coding=utf-8
from mxnet.gluon.data.dataset import Dataset
from mxnet.gluon.data.vision import transforms
from util import random_crop, random_rotate, random_scale, shrink_polys, parse_lines, save_images, random_horizontal_flip, process_data
import os
import glob
import cv2
from PIL import Image
import mxnet as mx
import numpy as np
from mxnet.gluon.data.vision import transforms

class ICDAR(Dataset):
    def __init__(self, data_dir, strides=4, input_size=(640, 640), num_kernels=6, debug=False):
        super(ICDAR, self).__init__()
        self.data_dir = data_dir
        self.imglst = glob.glob1(self.data_dir, '*g')
        self.length = len(self.imglst)
        self.input_size = input_size
        self.strides = strides
        self.num_kernel = num_kernels
        self.debug = debug
        self.trans = transforms.Compose([
            # transforms.RandomColorJitter(brightness = 32.0 / 255, saturation = 0.5),
            transforms.ToTensor(),
            transforms.Normalize([.485, .456, .406], [.229, .224, .225]),
        ])


    def __getitem__(self, item):
        img_name = self.imglst[item]
        prefix = ".".join(img_name.split('.')[:-1])
        label_name = prefix + '.txt'
        text_polys, text_tags = parse_lines(os.path.join(self.data_dir, label_name))
        im = cv2.imread(os.path.join(self.data_dir, img_name))
        # im = Image.open(os.path.join(self.data_dir, img_name)).convert('RGB')
        im = np.array(im)[:, :, :3]

        image, score_map, kernel_map, training_mask = process_data(im, text_polys, text_tags, self.num_kernel)
        if self.debug:
            im_show = np.concatenate([score_map*255, kernel_map[0, :, :]*255, kernel_map[1, :, :]*255, kernel_map[2, :, :]*255, training_mask*255], axis=1)
            cv2.imshow('img', image)
            cv2.imshow('score_map', im_show)
            cv2.waitKey()
        image = mx.nd.array(image)
        score_map = mx.nd.array(score_map, dtype=np.float32)
        kernal_map = mx.nd.array(kernel_map, dtype=np.float32)
        training_mask = mx.nd.array(training_mask, dtype=np.float32)
        trans_image = self.trans(image)
        return trans_image, score_map, kernel_map, training_mask, transforms.ToTensor()(image)

    def __len__(self):
        return self.length

if __name__ == '__main__':
    from mxnet.gluon.data import dataloader
    import sys
    
    root_dir = sys.argv[1]
    icdar = ICDAR(data_dir=root_dir, num_kernel=6, debug=True)
    loader = dataloader.DataLoader(dataset=icdar, batch_size=1)
    for k, item in enumerate(loader):
        img, score, kernel, training_mask, ori_img = item
        img = img.asnumpy()
        kernels = kernel.asnumpy()
        print img.shape, score.shape, img.max(), img.min()
        if k==10:
            break


