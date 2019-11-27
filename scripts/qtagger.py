import sys
import time
import getpass

import dtoolcore

from PyQt5.QtCore import Qt, QDir
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import (
    QAction,
    QComboBox,
    QDialog,
    QFileDialog,
    QInputDialog,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QApplication, QLabel, QMainWindow, QSizePolicy,
    QMenu
)

from ruamel.yaml import YAML


KEYMAP = {
    Qt.Key_1: 1,
    Qt.Key_2: 2,
    Qt.Key_3: 3,
    Qt.Key_4: 4,
    Qt.Key_5: 5
}

TAGMAP = {
    0: "Untagged",
    1: "Brown rust",
    2: "Yellow rust",
    3: "Septoria",
    4: "Mildew",
    5: "Healthy"
}


class TaggableImageSet(object):

    def __init__(self, uri):
        self.dataset = dtoolcore.DataSet.from_uri(uri)
        self.tags = {n: 0 for n in list(range(len(self.dataset.identifiers)))}
        self.load_times = {}
        self.tag_times = {}

    def save_to_file(self, fpath):

        with open(fpath, "w") as fh:
            fh.write("ImageNumber,FileName,TagID,TagLabel,Time\n")
            for n in range(len(self)):
                try:
                    tag_time = self.tag_times[n] - self.load_times[n]
                except KeyError:
                    tag_time = -1

                idn = list(self.dataset.identifiers)[n]
                fname = self.dataset.item_properties(idn)['relpath']
                fh.write(f"{n},{fname},{self.tags[n]},{TAGMAP[self.tags[n]]},{tag_time}\n")

    def __len__(self):
        return len(self.dataset.identifiers)

    def tag_item(self, index, tag):
        self.tags[index] = tag

        if index not in self.tag_times:
            self.tag_times[index] = time.time()

    def __getitem__(self, index):
        idn = list(self.dataset.identifiers)[index]
        image_fpath = self.dataset.item_content_abspath(idn)

        if index not in self.load_times:
            self.load_times[index] = time.time()

        return image_fpath


def get_available_datasets(fpath="data.yml"):
    yaml = YAML()

    with open("data.yml") as fh:
        result = yaml.load(fh)

    return result


class DataSetLoader(QDialog):

    def __init__(self):
        super(DataSetLoader, self).__init__()

        self.button = QPushButton("Load dataset")
        self.button.clicked.connect(self.finish)

        self.combobox = QComboBox(self)
        available_datasets = get_available_datasets()
        self.available_datasets = available_datasets
        self.combobox.addItems(available_datasets)

        layout = QVBoxLayout()
        layout.addWidget(self.combobox)
        layout.addWidget(self.button)

        self.setLayout(layout)

        self.show()

    def finish(self):
        self.accept()

    def getDataSet(self):
        ds_name = self.combobox.currentText()
        ds_uri = self.available_datasets[ds_name]

        return ds_name, ds_uri


class QTagger(QMainWindow):

    def __init__(self, uri=None):
        super(QTagger, self).__init__()

        # self.outputFileName = "results.csv"

        self.imageLabel = QLabel()
        self.imageLabel.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.imageLabel.setScaledContents(True)

        self.setCentralWidget(self.imageLabel)

        self.statusbar = self.statusBar()

        self.createActions()
        self.createMenus()

        if uri:
            self.load_dataset(uri)
        else:
            self.tis = None

        self.resize(600, 800)

    def load_dataset(self, uri):
        self.tis = TaggableImageSet(uri)
        self.image_index = 0
        self.set_image(self.image_index)
        self.update_statusbar()

        username = getpass.getuser()
        self.outputFileName = f"{username}-{self.tis.dataset.uuid}.csv"

    def set_image(self, idx):
        image_fpath = self.tis[idx]
        image = QImage(image_fpath)
        self.imageLabel.setPixmap(QPixmap.fromImage(image))

    def next_image(self):

        if self.image_index+1 < len(self.tis):
            self.image_index += 1
            self.set_image(self.image_index)

        self.update_statusbar()

    def prev_image(self):

        if self.image_index > 0:
            self.image_index -= 1
            self.set_image(self.image_index)

        self.update_statusbar()

    def update_statusbar(self):

        pos_label = f"Image [{self.image_index}/{len(self.tis)}]"
        # current_tag = self.tags[self.idns[self.image_index]]
        # tag_label = TAGMAP[current_tag]
        tag_label = f"{TAGMAP[self.tis.tags[self.image_index]]}"

        if self.image_index > 0:
            prev_tag_label = f"{TAGMAP[self.tis.tags[self.image_index-1]]}"
        else:
            prev_tag_label = "None"

        message = f"{pos_label} - ({tag_label}) - previous image ({prev_tag_label})"
        
        self.statusbar.showMessage(message)

    def createActions(self):
        self.openAct = QAction("&Open", self, shortcut="Ctrl+O", triggered=self.openURI)
        self.saveAct = QAction("&Save", self, shortcut="Ctrl+S", triggered=self.save)
        self.saveAsAct = QAction("Save &as", self, triggered=self.saveAs)
        self.helpAct = QAction("&Help", self, triggered=self.showhelp)

    def createMenus(self):
        self.fileMenu = QMenu("&File", self)
        self.fileMenu.addAction(self.openAct)
        self.fileMenu.addAction(self.saveAct)
        self.fileMenu.addAction(self.saveAsAct)
        self.menuBar().addMenu(self.fileMenu)

        self.helpMenu = QMenu("&Help", self)
        self.helpMenu.addAction(self.helpAct)
        self.menuBar().addMenu(self.helpMenu)

    def showhelp(self):

        tagMessage = "<p>Tag commands:</p>"
        "<ul>"
        for k, v in TAGMAP.items():
            tagMessage += f"<li>{k}: {v}</li>"
        tagMessage += "</ul>"

        QMessageBox.about(
            self,
            "Keyboard commands",
            tagMessage
        )

    def openURI(self):

        ds = DataSetLoader()
        if ds.exec_():
            ds_name, ds_uri = ds.getDataSet()
        else:
            ds_name, ds_uri = None, None

        if ds_uri:
            self.load_dataset(ds_uri)

    def save(self):
        self.tis.save_to_file(self.outputFileName)

    def saveAs(self):
        fileName, _ = QFileDialog.getSaveFileName(
            self,
            "Save Results",
            QDir.currentPath()
        )
        self.outputFileName = fileName
        self.save()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            sys.exit(0)

        if self.tis is not None:
            if event.key() == Qt.Key_Left:
                self.prev_image()

            if event.key() == Qt.Key_Right:
                self.next_image()

            if event.key() == Qt.Key_S:
                self.save()

            if event.key() in KEYMAP:
                tag_id = KEYMAP[event.key()]
                self.tis.tag_item(self.image_index, tag_id)
                self.next_image()


def main():

    if len(sys.argv) > 1:
        ds_uri = sys.argv[1]
    else:
        ds_uri = None

    app = QApplication([])
    qtagger = QTagger(ds_uri)
    qtagger.show()
    app.exec_()

if __name__ == "__main__":
    main()
