import sys
import time

import click
import dtoolcore

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import QApplication, QLabel, QMainWindow, QSizePolicy


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
        self.tags = {n: 'Untagged' for n in list(range(len(self.dataset.identifiers)))}
        self.load_times = {}
        self.tag_times = {}

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


class QTagger(QMainWindow):

    def __init__(self, ds):
        super(QTagger, self).__init__()

        self.ds = ds
        self.idns = list(ds.identifiers)
        self.tags = {idn: 0 for idn in self.idns}
        self.image_index = 0

        self.imageLabel = QLabel()
        self.imageLabel.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.imageLabel.setScaledContents(True)

        self.setCentralWidget(self.imageLabel)

        self.set_image(self.image_index)

        self.statusbar = self.statusBar()
        self.update_statusbar()

        self.resize(600, 800)

    def set_image(self, idx):
        idn = self.idns[idx]
        image_fpath = self.ds.item_content_abspath(idn)
        image = QImage(image_fpath)
        self.imageLabel.setPixmap(QPixmap.fromImage(image))

    def next_image(self):

        if self.image_index+1 < len(self.idns):
            self.image_index += 1
            self.set_image(self.image_index)

        self.update_statusbar()

    def prev_image(self):

        if self.image_index > 0:
            self.image_index -= 1
            self.set_image(self.image_index)

        self.update_statusbar()

    def update_statusbar(self):

        pos_label = f"Image [{self.image_index}/{len(self.idns)}]"
        current_tag = self.tags[self.idns[self.image_index]]
        tag_label = TAGMAP[current_tag]
        
        message = f"{pos_label} - ({tag_label})"
        
        self.statusbar.showMessage(message)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            sys.exit(0)

        if event.key() == Qt.Key_Left:
            self.prev_image()

        if event.key() in KEYMAP:
            tag_id = KEYMAP[event.key()]
            self.tags[self.idns[self.image_index]] = tag_id
            self.next_image()


@click.command()
@click.argument('dataset_uri')
def main(dataset_uri):

    ds = dtoolcore.DataSet.from_uri(dataset_uri)

    app = QApplication([])

    qtagger = QTagger(ds)
    qtagger.show()


    app.exec_()



if __name__ == "__main__":
    main()
