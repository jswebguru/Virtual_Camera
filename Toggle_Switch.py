import sys
from PySide6.QtCore import QRectF, QPropertyAnimation, QEasingCurve, Qt, Property, QSize
from PySide6.QtGui import QPainter, QColor, QPainterPath, QIcon
from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QApplication, QStyledItemDelegate, QStyle
from PySide6.QtCore import Signal


class ToggleSwitch(QWidget):
    @property
    def thumb_pos(self):
        return self._thumb_pos

    stateChanged = Signal(bool)  # Add this line to declare the signal

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(40, 20)
        self._checked = False

        self.thumb_rect = QRectF(2, 2, 16, 16)
        self._thumb_pos = 2.0

        self.animation = QPropertyAnimation(self, b"thumb_pos")
        self.animation.setDuration(10)
        self.animation.setEasingCurve(QEasingCurve.InOutQuad)

        self.setCursor(Qt.PointingHandCursor)

    def isChecked(self):
        return self._checked

    def setChecked(self, checked):
        self._checked = checked
        self.animation.setStartValue(self.thumb_pos)
        self.animation.setEndValue(22.0 if checked else 2.0)
        self.animation.start()
        self.stateChanged.emit(self._checked)  # Emit the signal when the state changes

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.setChecked(not self._checked)
            QWidget.mousePressEvent(self.parent(), event)

    @Property(float)
    def thumb_pos(self):
        return self._thumb_pos

    @thumb_pos.setter
    def thumb_pos(self, pos):
        self._thumb_pos = pos
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        track_color = QColor(0, 150, 0) if self.isChecked() else QColor(150, 150, 150)
        painter.setBrush(track_color)
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(0, 0, self.width(), self.height(), 10, 10)

        thumb_color = QColor(255, 255, 255)
        painter.setBrush(thumb_color)
        painter.setPen(Qt.NoPen)

        self.thumb_rect.moveLeft(self.thumb_pos)
        painter.drawEllipse(self.thumb_rect)


class LabeledToggleSwitch(QWidget):
    def __init__(self, label="Toggled_Switch", parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        self.switch = ToggleSwitch(self)
        self.label = QLabel(label, self)
        self.label.setStyleSheet("color: white; font-size: 14px;")
        layout.addWidget(self.switch)
        layout.addWidget(self.label)
        layout.addStretch()
        layout.setContentsMargins(0, 0, 0, 0)


class RoundedItemDelegate(QStyledItemDelegate):
    def __init__(self, radius=10, parent=None):
        super().__init__(parent)
        self.radius = radius

    def paint(self, painter, option, index):
        painter.save()

        # Setup the drawing rectangle
        rect = option.rect

        # Enable antialiasing for smoother curves
        painter.setRenderHint(QPainter.Antialiasing)

        # Determine background color based on selection
        bgColor = QColor(150, 150, 150) if option.state & QStyle.State_Selected else QColor(0, 0, 0)
        painter.setBrush(bgColor)
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(rect, self.radius, self.radius)

        # Attempt to draw the icon
        icon = index.data(Qt.DecorationRole)  # Fetch the icon
        if icon and isinstance(icon, QIcon):
            pixmap = icon.pixmap(140, 100, QIcon.Normal, QIcon.On)  # Only handle icons properly initialized
            image_rect = QRectF(rect).adjusted(5, 5, -5, -5).toRect()  # Adjust rect and convert to QRect for drawing

            # Create a clipping path for rounded corners
            clipPath = QPainterPath()
            clipPath.addRoundedRect(image_rect, self.radius, self.radius)
            painter.setClipPath(clipPath)
            if option.state & QStyle.State_Selected:
                painter.setOpacity(0.4)  # Set to 50% opacity for transparency

            # Draw the pixmap within the clipped path
            painter.drawPixmap(image_rect, pixmap)

        painter.restore()

    def sizeHint(self, option, index):
        return QSize(150, 120)  # Adjust based on your desired item geometry


if __name__ == '__main__':
    app = QApplication(sys.argv)

    window = LabeledToggleSwitch()
    window.show()
    sys.exit(app.exec())
