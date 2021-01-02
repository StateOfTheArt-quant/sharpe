#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import importlib
from typing import Iterable

import pandas as pd

import plotly.offline as py
import plotly.graph_objs as go


DEFAULT_CUSTOM_COLORS = ["#166761","#666666","#cc3399"]


class BaseGraph:
    """"""

    _name = None

    def __init__(
        self, df: pd.DataFrame = None, layout: dict = None, graph_kwargs: dict = None, name_dict: dict = None, **kwargs
    ):
        """
        :param df:
        :param layout:
        :param graph_kwargs:
        :param name_dict:
        :param kwargs:
            layout: dict
                go.Layout parameters
            graph_kwargs: dict
                Graph parameters, eg: go.Bar(**graph_kwargs)
        """
        self._df = df

        self._layout = dict() if layout is None else layout
        self._graph_kwargs = dict() if graph_kwargs is None else graph_kwargs
        self._name_dict = name_dict

        self.data = None

        self._init_parameters(**kwargs)
        self._init_data()

    def _init_data(self):
        """
        :return:
        """
        if self._df.empty:
            raise ValueError("df is empty.")

        self.data = self._get_data()

    def _init_parameters(self, **kwargs):
        """
        :param kwargs
        """

        # Instantiate graphics parameters
        self._graph_type = self._name.lower().capitalize()

        # Displayed column name
        if self._name_dict is None:
            self._name_dict = {_item: _item for _item in self._df.columns}

    @staticmethod
    def get_instance_with_graph_parameters(graph_type: str = None, **kwargs):
        """
        :param graph_type:
        :param kwargs:
        :return:
        """
        try:
            _graph_module = importlib.import_module("plotly.graph_objs")
            _graph_class = getattr(_graph_module, graph_type)
        except AttributeError:
            _graph_module = importlib.import_module("qlib.contrib.report.graph")
            _graph_class = getattr(_graph_module, graph_type)
        return _graph_class(**kwargs)

    @staticmethod
    def show_graph_in_notebook(figure_list: Iterable[go.Figure] = None):
        """
        :param figure_list:
        :return:
        """
        py.init_notebook_mode()
        for _fig in figure_list:
            # NOTE: displays figures: https://plotly.com/python/renderers/
            # default: plotly_mimetype+notebook
            # support renderers: import plotly.io as pio; print(pio.renderers)
            renderer = None
            try:
                # in notebook
                _ipykernel = str(type(get_ipython()))
                if "google.colab" in _ipykernel:
                    renderer = "colab"
            except NameError:
                pass

            _fig.show(renderer=renderer)

    def _get_layout(self) -> go.Layout:
        """
        :return:
        """
        return go.Layout(**self._layout)

    def _get_data(self) -> list:
        """
        :return:
        """

        _data = [
            self.get_instance_with_graph_parameters(
                graph_type=self._graph_type, x=self._df.index, y=self._df[_col], name=_name, **self._graph_kwargs
            )
            for _col, _name in self._name_dict.items()
        ]
        return _data

    @property
    def figure(self) -> go.Figure:
        """
        :return:
        """
        _figure = go.Figure(data=self.data, layout=self._get_layout())
        # NOTE: using default 3.x theme
        _figure["layout"].update(template=None)
        return _figure


class ScatterGraph(BaseGraph):
    _name = "scatter"


