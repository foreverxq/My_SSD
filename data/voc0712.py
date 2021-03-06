"""VOC Dataset Classes

Original author: Francisco Massa
https://github.com/fmassa/vision/blob/voc_dataset/torchvision/datasets/voc.py

Updated by: Ellis Brown, Max deGroot



"""
from utils.augmentations import SSDAugmentation
from data import *
# from config import HOME
import os.path as osp
import os
import sys
import torch
import torch.utils.data as data
import cv2
import numpy as np
from matplotlib import pyplot as plt
if sys.version_info[0] == 2:
    import xml.etree.cElementTree as ET
else:
    import xml.etree.ElementTree as ET


VOC_CLASSES = (  # always index 0
'8FSK','2FSK','AM','CW','8PSK'
)

# note: if you used our download scripts, this should be right
VOC_ROOT = r'D:\My_SSD\data\shipingtu\2'


class VOCAnnotationTransform(object):
    """Transforms a VOC annotation into a Tensor of bbox coords and label index
    Initilized with a dictionary lookup of classnames to indexes

    Arguments:
        class_to_ind (dict, optional): dictionary lookup of classnames -> indexes
            (default: alphabetic indexing of VOC's 20 classes)
        keep_difficult (bool, optional): keep difficult instances or not
            (default: False)
        height (int): height
        width (int): width
    """

    def __init__(self, class_to_ind=None, keep_difficult=False):
        self.class_to_ind = class_to_ind or dict(
            zip(VOC_CLASSES, range(len(VOC_CLASSES))))
        self.keep_difficult = keep_difficult

    def __call__(self, target, width, height):
        """
        Arguments:
            target (annotation) : the target annotation to be made usable
                will be an ET.Element
        Returns:
            a list containing lists of bounding boxes  [bbox coords, class name]
        """
        res = []
        for obj in target.iter('object'):
            difficult = int(obj.find('difficult').text) == 1
            if not self.keep_difficult and difficult:
                continue
            name = obj.find('name').text.lower().strip()
            bbox = obj.find('bndbox')

            pts = ['xmin', 'ymin', 'xmax', 'ymax']
            bndbox = []
            for i, pt in enumerate(pts):
                cur_pt = int(bbox.find(pt).text) - 1
                # scale height or width
                cur_pt = cur_pt / width if i % 2 == 0 else cur_pt / height
                bndbox.append(cur_pt)
            label_idx = self.class_to_ind[name.upper()]
            bndbox.append(label_idx)
            res += [bndbox]  # [xmin, ymin, xmax, ymax, label_ind]
            # img_id = target.find('filename').text[:-4]

        return res  # [[xmin, ymin, xmax, ymax, label_ind], ... ]


class VOCDetection(data.Dataset):
    """VOC Detection Dataset Object

    input is image, target is annotation

    Arguments:
        root (string): filepath to VOCdevkit folder.
        image_set (string): imageset to use (eg. 'train', 'val', 'test')
        transform (callable, optional): transformation to perform on the
            input image
        target_transform (callable, optional): transformation to perform on the
            target `annotation`
            (eg: take in caption string, return tensor of word indices)
        dataset_name (string, optional): which dataset to load
            (default: 'VOC2007')
    """

    def __init__(self, root,
                 transform=None, target_transform=VOCAnnotationTransform()):
        self.name = "xhjc_sjj"
        self.root = root
        self.transform = transform
        self.target_transform = target_transform
        self._annopath = osp.join(self.root,'xml', '%s.xml')
        self._imgpath = osp.join(self.root, '%s.bmp')
        self.ids = [i.split('.')[0] for i in os.listdir(osp.join(self.root, 'imag'))]



    def __getitem__(self, index):
        im, gt, h, w = self.pull_item(index)

        return im, gt

    def __len__(self):
        return len(self.ids)

    def pull_item(self, index):
        img_id = self.ids[index]

        target = ET.parse(self._annopath % img_id).getroot()
        #img = cv2.imread(self._imgpath % img_id)
        img = cv2.imread(osp.join(self.root, 'imag', img_id+'.bmp'),3)
        height, width, channels = img.shape

        if self.target_transform is not None:
            target = self.target_transform(target, width, height)

        if self.transform is not None:
            target = np.array(target)
            img, boxes, labels = self.transform(img, target[:, :4], target[:, 4])
            # to rgb
            img = img[:, :, (2, 1, 0)]
            # img = img.transpose(2, 0, 1)
            target = np.hstack((boxes, np.expand_dims(labels, axis=1)))
        return torch.from_numpy(img).permute(2, 0, 1), target, height, width
        # return torch.from_numpy(img), target, height, width

    def pull_image(self, index):
        '''Returns the original image object at index in PIL form

        Note: not using self.__getitem__(), as any transformations passed in
        could mess up this functionality.

        Argument:
            index (int): index of img to show
        Return:
            PIL img
        '''
        img_id = self.ids[index]
        # cv_img = cv2.imdecode(np.fromfile('C:/Users/华为/Desktop/ssd.pytorch-master/data/VOCdevkit/VOC2007/JPEGImages/w.jpg', dtype = np.uint8), -1)
        cv_img = cv2.imread(osp.join(self.root, 'imag', img_id+'.bmp'),3)
        return cv_img

    def pull_anno(self, index):
        '''Returns the original annotation of image at index

        Note: not using self.__getitem__(), as any transformations passed in
        could mess up this functionality.

        Argument:
            index (int): index of img to get annotation of
        Return:
            list:  [img_id, [(label, bbox coords),...]]
                eg: ('001718', [('dog', (96, 13, 438, 332))])
        '''
        img_id = self.ids[index]
        anno = ET.parse(self._annopath % img_id).getroot()
        gt = self.target_transform(anno, 1, 1)
        return img_id, gt

    def pull_tensor(self, index):
        '''Returns the original image at an index in tensor form

        Note: not using self.__getitem__(), as any transformations passed in
        could mess up this functionality.

        Argument:
            index (int): index of img to show
        Return:
            tensorized version of img, squeezed
        '''
        return torch.Tensor(self.pull_image(index)).unsqueeze_(0)

if __name__ == '__main__':
    MEANS = (104, 117, 123)
    min_dim = 300
    # testset = VOCDetection(VOC_ROOT, None, VOCAnnotationTransform())
    dataset = VOCDetection(root=VOC_ROOT,
                           transform=SSDAugmentation(min_dim,
                                                     MEANS))

    data_loader = data.DataLoader(dataset, 2,
                                  num_workers=2,
                                  shuffle=True, collate_fn=detection_collate,
                                  pin_memory=True)
    # create batch iterator
    batch_iterator = iter(data_loader)
    for i in range(100):

        try:
            # Samples the batch
            x, y = next(batch_iterator)
        except StopIteration:
            # restart the generator if the previous generator is exhausted.
            batch_iterator = iter(data_loader)
            x, y = next(batch_iterator)


    img_id = 10
    image = dataset.pull_image(img_id)
    rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    anno = dataset.pull_anno(img_id)
    tensor = dataset.pull_tensor(img_id)
    # View the sampled input image before transform
    item = dataset.pull_item(img_id)
    plt.figure(figsize=(10, 10))
    plt.imshow(rgb_image)
    plt.show()




