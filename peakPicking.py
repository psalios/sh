import nmrglue as ng
from collections import OrderedDict

from customBoxSelect import CustomBoxSelect
from tools.peakPickingSelectTool import PeakPickingSelectTool

from widgets.customButton import CustomButton

from bokeh.core.properties import Instance
from bokeh.embed import components
from bokeh.plotting import figure, show
from bokeh.models.sources import ColumnDataSource
from bokeh.models.widgets import Button, DataTable, TableColumn, Div, Paragraph
from bokeh.models.callbacks import CustomJS
from bokeh.models.markers import Circle
from bokeh.io import curdoc

class PeakPicking:

    def __init__(self, logger, dic, udic, pdata, dataSource):
        self.logger = logger

        self.dic = dic
        self.udic = udic
        self.pdata = pdata
        self.dataSource = dataSource

        self.sources = dict()
        self.sources['select'] = ColumnDataSource(data=dict(x=[], y=[], width=[], height=[]))
        self.sources['peaks'] = ColumnDataSource(data=dict(x=[], y=[]))

    def create(self):

        self.sources['table'] = ColumnDataSource(dict(x=[], y=[]))
        columns = [
                TableColumn(field="x", title="ppm"),
                TableColumn(field="y", title="y"),
            ]
        self.dataTable = DataTable(source=self.sources['table'], columns=columns, width=500)
        self.sources['table'].on_change('selected', lambda attr, old, new: self.rowSelect(new))

        self.auto = Button(label="Automatic Peak Picking", button_type="success", width=500)
        self.auto.on_click(self.autoPeakPicking)

        self.manual = CustomButton(label="Manual Peaks", button_type="primary", width=250, error="Please select area using the peak picking tool.")
        self.manual.on_click(self.manualPeakPicking)

        self.tool = CustomBoxSelect(self.logger, self.sources['select'], self.manual, selectTool=PeakPickingSelectTool)

        self.createResetButton()
        self.createDeselectButton()

        self.chemicalShiftReportTitle = Div(text="<strong>Chemical Shift Report</strong>")
        self.chemicalShiftReport = Paragraph(text=self.getMetadata())

    def getMetadata(self):
        return self.getLabel() + " NMR (" + self.getFrequency() + ", " + self.getSolvent() + ")"

    def getSolvent(self):
        return self.dic['acqus']['SOLVENT']

    def getLabel(self):
        return self.udic[0]['label']

    def getFrequency(self):
        return str(int(round(self.udic[0]['obs'], 0))) + " MHz"

    def createResetButton(self):
        self.resetButton = Button(label="Clear Selected Area", button_type="default", width=250)
        resetButtonCallback = CustomJS(args=dict(source=self.sources['select'], button=self.manual), code="""
            // get data source from Callback args
            var data = source.data;
            data['x'] = [];
            data['y'] = [];
            data['width'] = [];
            data['height'] = [];

            button.data = {};

            source.change.emit();
        """)
        self.resetButton.js_on_click(resetButtonCallback)

    def createDeselectButton(self):
        self.deselectButton = Button(label="Deselect all peaks", button_type="default", width=500)
        self.deselectButton.on_click(self.deselectData)

    def deselectData(self):
        self.sources['peaks'].data = dict(x=[], y=[])

    def autoPeakPicking(self):
        peaks = ng.peakpick.pick(self.pdata, 0)
        self.peaksIndices = [int(peak[0]) for peak in peaks]

        self.updateDataValues()


    def manualPeakPicking(self, dimensions):

        peaks = ng.peakpick.pick(self.pdata, dimensions['y0'])
        self.peaksIndices = [int(peak[0]) for peak in peaks]

        # Filter top
        self.peaksIndices = [i for i in self.peaksIndices if self.pdata[i] <= dimensions['y1']]
        # Filter left
        self.peaksIndices = [i for i in self.peaksIndices if self.dataSource.data['ppm'][i] <= dimensions['x0']]
        # Filter right
        self.peaksIndices = [i for i in self.peaksIndices if self.dataSource.data['ppm'][i] >= dimensions['x1']]

        if len(self.peaksIndices) > 0:
            self.updateDataValues()

        # Clear selected area
        self.sources['select'].data = dict(x=[], y=[], width=[], height=[])

    def updateDataValues(self):
        # Update DataTable Values
        newData = list(OrderedDict.fromkeys(
            zip(
                self.sources['table'].data['x'] + [self.dataSource.data['ppm'][i] for i in self.peaksIndices],
                self.sources['table'].data['y'] + [self.pdata[i] for i in self.peaksIndices]
            )
        ))
        newX, newY = zip(*newData)
        self.sources['table'].data = {
            'x': newX,
            'y': newY
        }

    def rowSelect(self, rows):
        ids = rows['1d']['indices']
        self.sources['peaks'].data = {
            'x': [self.sources['table'].data['x'][i] for i in ids],
            'y': [self.sources['table'].data['y'][i] for i in ids]
        }

    def draw(self, plot):
        circle = Circle(
            x="x",
            y="y",
            size=10,
            line_color="#ff0000",
            fill_color="#ff0000",
            line_width=1
        )
        plot.add_glyph(self.sources['peaks'], circle, selection_glyph=circle, nonselection_glyph=circle)

        self.tool.addTool(plot)
        self.tool.addGlyph(plot, "#009933")
