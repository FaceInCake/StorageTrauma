"Contains a single class `ImageDownloader`, use the public methods for fetching Icons and Sprites. It will cache sprite sheets so try to do it in batches."

from functools import cache
from os import makedirs, remove, listdir
from os.path import split as path_split, isdir, isfile, join as path_join
from typing import Final
from BaroInterface import Texture, Colour, Item, WHITE
from glob import glob
from re import compile
from numpy import multiply # Epic math
from cv2 import resize, imread, imwrite, IMREAD_UNCHANGED # OpenCV image editing tools, yes its a bit overkill, bite me
from cv2.typing import MatLike

def __validate_path (target:str) -> str:
    "recursive helper function for `path_to`"
    if isdir(target): return target
    head, tail = path_split(target)
    if head=='':
        raise IOError(f"Invalid directory '{target}'")
    head = __validate_path(head)
    re_tail = compile('(?i)'+tail)
    candidates = listdir(head)
    for test in candidates:
        if m := re_tail.match(test):
            return head+'/'+m[0]
    raise IOError(f"Invalid directory '{tail}' at '{head}'")

def path_to (targetPath:str) -> str:
    "Will attempt to find the file at the given path. Checks for case-sensitivity"
    targetPath = targetPath.replace('\\', '/') # modern windows is fine with forward-slashes 
    if isfile(targetPath): return targetPath
    head, tail = path_split(targetPath)
    head = __validate_path(head)
    re_tail = compile('(?i)'+tail)
    candidates = listdir(head)
    for test in candidates:
        if (m := re_tail.match(test)):
            return head + '/' + m[0]
    raise IOError(f"Invalid file name '{tail}' at '{head}'")

class ImageDownloader:
    "Construct me with the rootDir in order to call `download_sprites/icons`"
    ICON_SIZE :Final[int] = 64

    def __init__(self, rootDir:str) -> None:
        self.__rootDir = rootDir

    @cache
    def __get_img (self, filePath:str) -> MatLike:
        "Fetches the given sprite sheet, also caches it for re-use"
        target = path_join(self.__rootDir, filePath)
        act = path_to(target)
        img = imread(act, IMREAD_UNCHANGED)
        return img

    def __prepare_folder (self, dir:str):
        "Makes and clears the given directory path"
        makedirs(dir, exist_ok=True)
        all(remove(p) for p in glob(f"{dir}/*.png")) # should only be PNGs
    
    def __get_resize (self, i:Texture) -> tuple[int,int]:
        """Soley used when needing to use an items Sprite for their Icon,
        calculates the new smaller size while maintaining aspect ratio"""
        S = ImageDownloader.ICON_SIZE # shorthand
        w, h = tuple(i.rect[2:4])
        return (S, round(S*h/w)) if w > h else (round(S*w/h), S)

    @staticmethod
    def __crop (img:MatLike, rect:tuple[int,int,int,int]) -> MatLike:
        """Crops the given opencv `img` using the given xywh `rect`, returns the result"""
        return img[rect[1]:rect[1]+rect[3], rect[0]:rect[0]+rect[2]]

    @staticmethod
    def __colour_image (img:MatLike, colour:Colour) -> MatLike:
        if colour != WHITE:
            c = list(colour)
            c.reverse() # RGB -> BGR
            return multiply(img[:,:], [*c, 1.0])
        return img

    def download_sprites (self, items:dict[str,Item], targetDir:str) -> bool:
        "Attempts to download the sprites for the given `items`, looking in `self.rootDir`, exporting to `targetDir`"
        self.__prepare_folder(targetDir)
        return all(
            imwrite(
                f"{targetDir}/{id}.png",
                self.__colour_image(
                    self.__crop(
                        self.__get_img(item.sprite.path),
                        item.sprite.rect),
                    item.sprite.colour)
            ) for id, item in items.items()
        )    

    def download_icons (self, items:dict[str,Item], targetDir:str) -> bool:
        "Attempts to download the icons for the given `items`, same as download_icons, but backs up to resized sprites if needed"
        self.__prepare_folder(targetDir)
        return all(
            imwrite(
                f"{targetDir}/{id}.png",
                self.__colour_image(
                    resize(
                        self.__crop(
                            self.__get_img(item.icon.path),
                            item.icon.rect),
                        self.__get_resize(item.icon)),
                    item.icon.colour),
            ) if item.icon is not None else
            imwrite(
                f"{targetDir}/{id}.png",
                self.__colour_image(
                    resize(
                        self.__crop(
                            self.__get_img(item.sprite.path),
                            item.sprite.rect),
                        self.__get_resize(item.sprite)),
                    item.sprite.colour)
            ) for id, item in items.items()
        )
# end ImageDownloader
