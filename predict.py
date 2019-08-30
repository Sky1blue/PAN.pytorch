# -*- coding: utf-8 -*-
# @Time    : 2019/8/24 12:06
# @Author  : zhoujun

import torch
from torchvision import transforms
import os
import cv2
import time
import numpy as np

from models import get_model


class Pytorch_model:
    def __init__(self, model_path, gpu_id=None):
        '''
        初始化pytorch模型
        :param model_path: 模型地址(可以是模型的参数或者参数和计算图一起保存的文件)
        :param gpu_id: 在哪一块gpu上运行
        '''
        self.gpu_id = gpu_id
        checkpoint = torch.load(model_path)

        if self.gpu_id is not None and isinstance(self.gpu_id, int) and torch.cuda.is_available():
            self.device = torch.device("cuda:%s" % self.gpu_id)
        else:
            self.device = torch.device("cpu")
        print('device:', self.device)

        config = checkpoint['config']
        self.net = get_model(config)

        self.img_channel = config['data_loader']['args']['dataset']['img_channel']
        self.net.load_state_dict(checkpoint['state_dict'])
        self.net.to(self.device)
        self.net.eval()

    def predict(self, img: str, long_size: int = 2240):
        '''
        对传入的图像进行预测，支持图像地址,opecv 读取图片，偏慢
        :param img: 图像地址
        :param is_numpy:
        :return:
        '''
        assert os.path.exists(img), 'file is not exists'
        img = cv2.imread(img)
        if self.img_channel == 3:
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        h, w = img.shape[:2]
        scale = long_size / max(h, w)
        img = cv2.resize(img, None, fx=scale, fy=scale)
        # 将图片由(w,h)变为(1,img_channel,h,w)
        tensor = transforms.ToTensor()(img)
        tensor = tensor.unsqueeze_(0)

        tensor = tensor.to(self.device)
        with torch.no_grad():
            start = time.time()
            preds = self.net(tensor)[0]
            preds[:2] = torch.sigmoid(preds[:2])
            preds = preds.cpu().numpy()
            t = time.time() - start
        return preds, t

if __name__ == '__main__':
    import matplotlib.pyplot as plt
    from utils.util import show_img

    os.environ['CUDA_VISIBLE_DEVICES'] = str('2')

    model_path = 'output/PAN_resnet18/checkpoint/model_best.pth'

    # model_path = 'output/psenet_icd2015_new_loss/final.pth'
    img_id = 10
    img_path = '/data1/ocr/icdar2015/test/img/img_{}.jpg'.format(img_id)

    # 初始化网络
    show_img(cv2.imread(img_path)[:,:,::-1],color=True)
    model = Pytorch_model(model_path,  gpu_id=0)
    preds, t = model.predict(img_path)
    show_img(preds)
    plt.show()
