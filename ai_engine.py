import codecs
import os
import yaml
import numpy as np
import cv2
import paddle
from paddle.inference import create_predictor
from paddle.inference import Config as PredictConfig
import paddleseg.transforms as T
from paddleseg.core.infer import reverse_transform
from paddleseg.cvlibs import manager


class DeployConfig:

    def __init__(self, path):
        with codecs.open(path, 'r', 'utf-8') as file:
            self.dic = yaml.load(file, Loader=yaml.FullLoader)

        self._transforms = self._load_transforms(self.dic['Deploy'][
            'transforms'])
        self._dir = os.path.dirname(path)

    @property
    def transforms(self):
        return self._transforms

    @property
    def model(self):
        return os.path.join(self._dir, self.dic['Deploy']['model'])

    @property
    def params(self):
        return os.path.join(self._dir, self.dic['Deploy']['params'])

    def target_size(self):
        [width, height] = self.dic['Deploy']['transforms'][0]['target_size']
        return [width, height]

    def _load_transforms(self, t_list):
        com = manager.TRANSFORMS
        transforms = []
        for t in t_list:
            ctype = t.pop('type')
            transforms.append(com[ctype](**t))

        return transforms


class Predictor:

    def __init__(self, args):
        self.args = args
        self.cfg = DeployConfig(args.config)
        self.compose = T.Compose(self.cfg.transforms)

        pred_cfg = PredictConfig(self.cfg.model, self.cfg.params)
        pred_cfg.disable_glog_info()
        pred_cfg.disable_gpu()
        self.predictor = create_predictor(pred_cfg)

    def run(self, img, bg, only_mask=False):
        input_names = self.predictor.get_input_names()
        input_handle = self.predictor.get_input_handle(input_names[0])
        data = self.compose({'img': img})
        input_data = np.array([data['img']])

        input_handle.reshape(input_data.shape)
        input_handle.copy_from_cpu(input_data)

        self.predictor.run()
        output_names = self.predictor.get_output_names()
        output_handle = self.predictor.get_output_handle(output_names[0])
        output = output_handle.copy_to_cpu()

        return self.postprocess(output, img, data, bg, only_mask)

    def postprocess(self, pred_img, origin_img, data, bg, only_mask=False):
        trans_info = data['trans_info']
        score_map = pred_img[0, 1, :, :]

        score_map = score_map[np.newaxis, np.newaxis, ...]
        score_map = reverse_transform(
            paddle.to_tensor(score_map), trans_info, mode='bilinear')
        alpha = np.transpose(score_map.numpy().squeeze(1), [1, 2, 0])
        alpha = np.squeeze(alpha, axis=-1)

        if only_mask:
            return alpha
        h, w, _ = origin_img.shape
        bg = cv2.resize(bg, (w, h))
        if bg.ndim == 2:
            bg = bg[..., np.newaxis]

        out = (alpha * origin_img + (1 - alpha) * bg).astype(np.uint8)
        return out

