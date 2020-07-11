# To add a new cell, type '# %%'
# To add a new markdown cell, type '# %% [markdown]'
# %%
# Import Libraries
import pandas as pd
import numpy as np
import json
import networkx as nx
import plotly.graph_objects as go
from matplotlib import cm
from matplotlib.colors import ListedColormap, LinearSegmentedColormap 
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
from datetime import datetime as dt

import socket
print(socket.gethostname())

# Stylesheet
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)


# Load  Data
df =pd.read_csv("data.csv")

#Color scale of edges
viridis = cm.get_cmap('viridis', 12)
# Define Color
df['Dura_color']=(df['Duration']/df['Duration'].max()).apply(viridis)
df['Date']=df['Date'].apply(pd.to_datetime).dt.date

#### Plots
# Plot Graph of calls
def plot_network(df):
    nodes=np.union1d(df['Caller'].unique(),df['Receiver'].unique())
    print(nodes.shape[0])

    G = nx.random_geometric_graph(nodes.shape[0], 0.125)
    df['Caller_node']=df['Caller'].apply(lambda x:list(nodes).index(x))
    df['Receiver_node']=df['Receiver'].apply(lambda x:list(nodes).index(x))
    # Add Edges to Plot
    edge_trace=[]
    def add_coords(x): 
        x0,y0=G.nodes[x['Caller_node']]['pos']
        x1,y1=G.nodes[x['Receiver_node']]['pos']
        edge_trace.append(dict(type='scatter',
        x=[x0,x1], y=[y0,y1],
        line=dict(width=0.5, color='rgba'+str(x['Dura_color'])),
        hoverinfo='none',
        mode='lines'))
    df.apply(add_coords,axis=1)
    ## adding points
    node_x = []
    node_y = []
    for node in G.nodes():
        x, y = G.nodes[node]['pos']
        node_x.append(x)
        node_y.append(y)
    node_trace = go.Scatter(
        x=node_x, y=node_y,
        mode='markers',
        hoverinfo='text',
        marker=dict(
            size=10,
            line_width=2))
    fig = go.Figure(data=edge_trace+[node_trace],
                layout=go.Layout(
                    title='<br>Phone Calls Made',
                    titlefont_size=16,
                    showlegend=False,
                    hovermode='closest',
                    margin=dict(b=20,l=5,r=5,t=40),
                    annotations=[ dict(
                        showarrow=True,
                        xref="paper", yref="paper",
                        x=0.005, y=-0.002 ) ],
                    xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                    yaxis=dict(showgrid=False, zeroline=False, showticklabels=False))
                    )
    fig.update_layout(transition_duration=500)
    return fig








#Apps default variables
default_duration_slider_val = [0,10]
default_time_slider_val = ['00:00', '24:00']


#Loop to generate marks for Time
time_str = ['0','0',':','0','0']
times = {0:"".join(time_str)}
for i in range(0,48):
    if i%2 == 0:
        time_str[3] = '3'
    else:
        time_str = list( str(int("".join(time_str[0:2]) ) + 1 ).zfill(2) + str(':00') )
    times[i+1] = "".join(time_str)








# Layout of App
app.layout = html.Div(children=[
    html.H1(children='CDR Analyser'),

    html.Div(children='''
        Analyse the phone calls between people.
    '''),
    html.Div(
        id='date-selected'
    ),
    dcc.Graph(
        id='network-plot',
        figure=plot_network(df[df['Date']==df['Date'].min()].reset_index(drop=True))
    ),
    dcc.DatePickerSingle(
        id='date-picker',
        min_date_allowed=df['Date'].min(),
        max_date_allowed=df['Date'].max(),   
        initial_visible_month=dt(2020, 6, 5),
        date=str(dt(2020, 6, 5, 0, 0, 0 )) 
    ),
    
    
    dcc.RangeSlider(
        id='duration-slider',
        min=0,
        max=df['Duration'].max(),
        step=1,
        value=default_duration_slider_val,
        dots=True,
        
    ),
    
    dcc.RangeSlider(
        id='time-slider',
        min=0,
        max= 48,
        step=None,
        marks=times,
        dots=True,
        value = [0,48],
        pushable=1
        
    ),
    
    

    
    html.Div(id='duration-slider-output-container', children="Duration selected : {} to {} units".format(default_duration_slider_val[0], default_duration_slider_val[1])),

    html.Div(id='time-slider-output-container', children="Time of Day selected : {} to {} hours".format(default_time_slider_val[0], default_time_slider_val[1]))
    
    
])

# Callbacks
@app.callback(
    Output(component_id='network-plot', component_property='figure'),
    
    [Input(component_id='date-picker', component_property='date'), Input(component_id='duration-slider', component_property='value'), Input(component_id='time-slider', component_property='value')]
)
def update_output_div(selected_date, selected_duration, selected_time):
    """
    This callback is used to update:
    1) The main graph by changing it's linked dataframe by 'date' and 'Duration' currently selected.
    """
    
    print('Callback Called')

    print('selected_date', selected_date)
    print('selected_duration', selected_duration)
    print('selected_time', selected_time)
    # ^^^^ For debugging purposes only 
    
    
    #Handling Date
    date_filt_df=df[df['Date']==pd.to_datetime(selected_date)].reset_index(drop=True)
    
    #Handling Duration of call
    dur_date_filt_df = date_filt_df[ (date_filt_df['Duration'] >= selected_duration[0]) & (date_filt_df['Duration'] <= selected_duration[1]) ]
    
    #Handling Time of Day
    time_dur_date_filt_df = dur_date_filt_df[ (dur_date_filt_df['Time'] < times[selected_time[1]]) & (dur_date_filt_df['Time'] >= times[selected_time[0]]) ]
    
    return plot_network(time_dur_date_filt_df)





@app.callback(
    Output(component_id='duration-slider-output-container', component_property='children'),
    
    [Input(component_id='duration-slider', component_property='value')]    
)
def update_selected_duration(selected_duration):
    """
    This callback is used to update:
    1) The string which denotes the currently selected duration. 
    2) The string which denotes the currently selected time
    """
    return "Duration selected : {} to {} units".format(selected_duration[0], selected_duration[1])



@app.callback(
    Output(component_id='time-slider-output-container', component_property='children'),
    
    [Input(component_id='time-slider', component_property='value')]    
)
def update_selected_duration(selected_time):
    """
    This callback is used to update:
    1) The string which denotes the currently selected time.
    """
    return "Time of Day selected : {} to {} hours".format(times[selected_time[0]], times[selected_time[1]])








# Run Server
if __name__ == '__main__':
    #app.run_server(debug=True, port=8000)
    app.run_server(debug = True,host='0.0.0.0')
