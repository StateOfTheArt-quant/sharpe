from plotly.offline import plot
from sharpe.utils.plot.base import ScatterGraph, DEFAULT_CUSTOM_COLORS

def plot_performance(df, auto_open=True):
    layout=dict(title="unit net value", xaxis=dict(type="category", tickangle=45))
    graph_kwargs = {"line":dict(width=3,smoothing=1,shape="spline")}
    fig = ScatterGraph(df, layout=layout, graph_kwargs=graph_kwargs)
    figure = fig.figure
    
    # update default custom color
    for i, trace in enumerate(figure["data"]):
        trace["line"]["color"] = DEFAULT_CUSTOM_COLORS[i]
        if i >= len(DEFAULT_CUSTOM_COLORS) - 1:
            break
    plot(figure, auto_open=auto_open)
    
    return figure
    #plot(figure, auto_open=True)
    #pass

if __name__ == "__main__":
    pass