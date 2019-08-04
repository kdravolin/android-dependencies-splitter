import os
import shutil
import ssl
import urllib.request
import zipfile
from distutils.dir_util import copy_tree
from os.path import join as path


class DIR:
    BUILD = 'build'
    OUT = 'out'
    DEPENDENCIES = 'dependencies.list'

    AAR = path(BUILD, 'aar')
    JAR = path(BUILD, 'jar')
    UNZIPPED_AAR = path(BUILD, 'unzippedAar')
    UNZIPPED_JAR = path(BUILD, 'unzippedJar')
    MERGED_CLASSES = path(BUILD, 'mergedClasses')
    LIB_JAR = path(OUT, 'androidx-classes')

    ANDROID_PROJECT = 'android-project'
    MERGED_RES = path(ANDROID_PROJECT, 'androidx/build/intermediates/res/merged/release')
    PROJECT_RES = path(ANDROID_PROJECT, 'androidxres/src/main/res')
    PROJECT_AAR = path(ANDROID_PROJECT, 'androidxres/build/outputs/aar/androidxres-release.aar')
    LIB_AAR = path(OUT, 'androidx-resources.aar')

    @staticmethod
    def clear():
        clear_dir(DIR.AAR)
        clear_dir(DIR.JAR)
        clear_dir(DIR.MERGED_CLASSES)
        clear_dir(DIR.UNZIPPED_AAR)
        clear_dir(DIR.UNZIPPED_JAR)
        clear_dir(DIR.PROJECT_RES)
        clear_dir(DIR.OUT)


class Dependency:
    _name = ""
    group = ""
    module = ""
    version = ""
    maven_aar = ""

    def __init__(self, name):
        self._name = name

        split_name = name.split(':')
        self.group = split_name[0]
        self.module = split_name[1]
        self.version = split_name[2]

        file_name = '%s_%s_%s' % (self.group, self.module, self.version)

        maven = 'http://maven.google.com/{0}/{1}/{2}/{1}-{2}'.format(
            self.group.replace('.', '/'),
            self.module,
            self.version
        )
        self.maven_aar = '%s.aar' % maven
        self.maven_jar = '%s.jar' % maven

        self.aar = '%s/%s.aar' % (DIR.AAR, file_name)
        self.unzipped = path(DIR.UNZIPPED_AAR, file_name)
        self.unzipped_jar = path(DIR.UNZIPPED_JAR, file_name)
        self.classes = path(self.unzipped, 'classes.jar')
        self.jar = '%s/%s.jar' % (DIR.JAR, file_name)


def prepare_aar(dependency):
    urllib.request.urlretrieve(dependency.maven_aar, dependency.aar)

    with zipfile.ZipFile(dependency.aar, 'r') as zip_ref:
        zip_ref.extractall(dependency.unzipped)

    shutil.copyfile(dependency.classes, dependency.jar)


def prepare_jar(dependency):
    urllib.request.urlretrieve(dependency.maven_jar, dependency.jar)


def copytree(src, dst, symlinks=False, ignore=None):
    for item in os.listdir(src):
        s = os.path.join(src, item)
        d = os.path.join(dst, item)
        if os.path.isdir(s):
            shutil.copytree(s, d, symlinks, ignore)
        else:
            shutil.copy2(s, d)


def prepare_classes(dependency):
    with zipfile.ZipFile(dependency.jar, 'r') as zip_ref:
        zip_ref.extractall(dependency.unzipped_jar)

    copy_tree(dependency.unzipped_jar, DIR.MERGED_CLASSES)


def prepare_lib(name):
    dependency = Dependency(name)

    try:
        prepare_aar(dependency)
    except:
        prepare_jar(dependency)

    prepare_classes(dependency)


def prepare_merged_jar():
    shutil.make_archive(DIR.LIB_JAR, 'zip', DIR.MERGED_CLASSES)
    os.rename(DIR.LIB_JAR + '.zip', DIR.LIB_JAR + '.jar')


def clear_dir(path):
    if os.path.exists(path):
        shutil.rmtree(path)
    os.makedirs(path)


def gradlew(cmd):
    os.chdir(DIR.ANDROID_PROJECT)
    os.system('./gradlew %s' % cmd)
    os.chdir('../')


def prepare_resources_aar():
    gradlew(':androidx:assembleRelease')
    copy_tree(DIR.MERGED_RES, DIR.PROJECT_RES)
    gradlew(':androidxres:assembleRelease')
    shutil.copyfile(DIR.PROJECT_AAR, DIR.LIB_AAR)


def read_dependencies():
    with open(DIR.DEPENDENCIES) as f:
        dependencies = [line.rstrip('\n') for line in f]
    return dependencies


def main():
    ssl._create_default_https_context = ssl._create_unverified_context
    DIR.clear()

    for depend in read_dependencies():
        prepare_lib(depend)

    prepare_merged_jar()
    prepare_resources_aar()


main()
