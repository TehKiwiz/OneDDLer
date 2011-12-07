import os

class FolderManagment:
    def __init__(self, main_folder):
        self.__root = main_folder

    def get_folder(self, show_name):
        dirs = os.listdir(self.__root)
        returnDir = ''
        for f in dirs:
            if f.lower().find(show_name.lower()) != -1:
                return '\\'.join( (self.__root, f) )
        returnDir = '\\'.join( (self.__root, show_name))
        os.mkdir(returnDir)
        return returnDir
