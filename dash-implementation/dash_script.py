#### Import Libraries #########
import pandas as pd
import base64
import io
import numpy as np
import json
import networkx as nx
import plotly.graph_objects as go
from matplotlib import cm
from matplotlib.colors import ListedColormap, LinearSegmentedColormap
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
from datetime import datetime as dt
from stats import *
import pygraphviz as pgv
import dash_bootstrap_components as dbc
import math
### Import functions for Breadth First Search ###
from addEdge import addEdge

from BFSN import bfs

##### Stylesheet #####
external_stylesheets = [dbc.themes.SANDSTONE]


# Load  Data
df = pd.read_csv('./data/data.csv')
df2 = pd.read_csv('./data/ipdr_data.csv')

#### Create App ###
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
app.title = 'CDR/IPDR Analyser'
#### Default Variables ####
default_duration_slider_val = [0, 100]
default_time_slider_val = ['00:00', '24:00']
# Loop to generate marks for Time
time_str = ['0', '0', ':', '0', '0']
times = {0: {'label': "".join(time_str), "style": {
    "transform": "rotate(-90deg) translateY(-15px)"}}}
for i in range(0, 48):
    if i % 2 == 0:
        time_str[3] = '3'
        times[i+1] = {'label': "".join(time_str), "style": {'display': 'none'}}
    else:
        time_str = list(
            str(int("".join(time_str[0:2])) + 1).zfill(2) + str(':00'))
        times[i+1] = {'label': "".join(time_str),
                      "style": {"transform": "rotate(-90deg) translateY(-15px)"}}
# Generating marks for duration slider
durations = {}
for i in range(0, df['Duration'].max(), 5):
    durations[i] = str(i)


coords_to_node = {}  # Dictionary that stores coordinates to node number

node_to_num = {}  # Dictionary that stores node number to phone number
num_to_node = {}  #Dictionary that stores numbers to node
data_columns = ["Caller", "Receiver", "Date",
                "Time", "Duration", "TowerID", "IMEI"]

data_columns_ipdr = ["IMEI","Private IP","Private Port", "Public IP", "Public Port", "Dest IP","DEST PORT", "MSISDN", "IMSI", "Start Date","Start Time",\
    "End Date","End Time", "CELL_ID", "Uplink Volume","Downlink Volume","Total Volume","I_RATTYPE"]


ports_to_apps = {'DEST PORT':'App','5223':'WhatsApp','5228':'WhatsApp', '4244':'WhatsApp', '5222':'WhatsApp', '5242':'WhatsApp','443':'Skype',\
    '3478-3481':'Skype','49152-65535':'Skype','80':'Web connection','8080':'Web Connection', \
        '8081': 'Web Connection', '993':'IMAP', '143':'IMAP', '8024':'iTunes', '8027':'iTunes', '8013':'iTunes', \
            '8017':'iTunes', '8003':'iTunes', '7275':'iTunes', '8025':'iTunes', '8009':'iTunes',\
                '58128': 'Xsan', '51637':'Xsan', '61076':'Xsan','40020':'Microsoft Online Games', '40017':'Microsoft Various Games', \
                    '40023':'Microsoft Online Games',\
                    '40019':'Microsoft Online Games', '40001':'Microsoft Online Games', '40004':'Microsoft Online Games', \
                        '40034':'Microsoft Online Games', '40031':'Microsoft Online Games', '40029':'Microsoft Online Games',\
                              '40005':'Microsoft Online Games', '40026': 'Microsoft Online Games', '40008': 'Microsoft Online Games',\
                                  '40032':'Microsoft Online Games'}   # did not take '443':'SSL, Web connection' to avoid double 443


# Color scale of edges
viridis = cm.get_cmap('viridis', 12)
def preprocess_data(df,df2):
    # nodes
    nodes = np.union1d(df['Caller'].unique(), df['Receiver'].unique())
    # Define Color
    df['Dura_color'] = (df['Duration']/df['Duration'].max()).apply(viridis)
    df['Date'] = df['Date'].apply(pd.to_datetime).dt.date


    df['Caller_node'] = df['Caller'].apply(
        lambda x: list(nodes).index(x))  # Caller Nodes
    
    df['Receiver_node'] = df['Receiver'].apply(lambda x: list(nodes).index(x))

    df2['IMEI_node'] = df2['IMEI'].apply(lambda x: list(nodes).index(x))
    df2['App_name'] = df2['DEST PORT'].apply(lambda x:ports_to_apps[str(x)])

    coords_to_node.clear()
    num_to_node.clear()
    node_to_num.clear()

preprocess_data(df,df2)
#### Plots ####
# Plot Graph of calls

fig = go.Figure()
pos = {}

def plot_network(df):
    G = nx.DiGraph()  # networkX Graph
    # Reciever Nodes

    def make_graph(x):
        G.add_edge(x["Caller_node"], x["Receiver_node"])

    df.apply(make_graph, axis=1)  # Make a graph
    pos = nx.nx_agraph.graphviz_layout(G)  # Position of Points

    # Add Edges to Plot
    edge_trace = []

    def add_coords(x):
        x0, y0 = pos[x['Caller_node']]
        x1, y1 = pos[x['Receiver_node']]

        node_to_num[x['Caller_node']] = x['Caller']
        node_to_num[x['Receiver_node']] = x['Receiver']
        num_to_node[x['Caller']] = x['Caller_node']
        num_to_node[x['Receiver']] = x['Receiver_node']
        edges_x,edges_y=addEdge((x0,y0),(x1,y1),[],[])
        edge_trace.append(dict(type='scatter',
                               x=edges_x, y=edges_y,
                               showlegend=False,
                               line=dict(
                                   width=2, color='rgba'+str(x['Dura_color']).replace(']', ')').replace('[', '(')),
                               hoverinfo='none',
                               mode='lines',
        ))  # Graph object for each connection
       
    df.apply(add_coords, axis=1)  # Adding edges

    # adding points
    node_x = []
    node_y = []
    total_duration = []
    hover_list = []
    for node in pos:
        x, y = pos[node]
        coords_to_node[(x, y)] = node
        hover_list.append(str(node_to_num[node]))
        node_x.append(x)
        node_y.append(y)
        total_duration.append(27*pow((df[(df['Caller_node']==node)|(df['Receiver_node']==node)]['Duration'].sum())/df['Duration'].max(),0.3))
    node_trace = go.Scatter(
        x=node_x, y=node_y,
        mode='markers',
        hovertext = hover_list,
        hoverinfo='text',
        showlegend=False,
        marker=dict(
            size=total_duration,
            showscale=True,
            line_width=2,
            line_color='black'))  # Object for point scatter plot
    fig = go.Figure(data=edge_trace+[node_trace],
                    layout=go.Layout(
                   
                    titlefont_size=16,
                 

                    hovermode='closest',
                    margin=dict(b=20, l=5, r=5, t=40),
                    annotations=[dict(
                        showarrow=True,
                        xref="paper", yref="paper",
                        x=0.005, y=-0.002)],
                    xaxis=dict(showgrid=False, zeroline=False,
                               showticklabels=False),
                    yaxis=dict(showgrid=False, zeroline=False, showticklabels=False))
                    )  # Complete Figure
    fig.update_layout(transition_duration=500)  # Transition
    #fig.update_layout(hover_label_align = 'right')
    fig.update_layout(
         hoverlabel = dict(bgcolor='white',font_size = 15,font_family = 'Rockwell')
    )
    # fig.update_layout(clickmode='event+select')  # Event method
    fig.update_layout(yaxis = dict(scaleanchor = "x", scaleratio = 1), plot_bgcolor='rgb(255,255,255)')
    #fig.update_traces(marker_size=20)  # marker size
    return fig

# Create an image for the same. -- What?


##### Layout of App #####
app.layout = html.Div(children=[

    #Child 1
    html.Div(children=[
        html.H1(children='CDR Analyser'),  # Title
        html.H3(children='''
        Analyse the phone calls between people.
    '''),  # Subtitle
        html.Div(
            id='date-selected'
        ),  # Date Selected Indicator
        html.H4(id='message'),  # Message
    ],id='header-text'),

    #Child 2
    dbc.Row(children=[

        #Child 2.1
        dbc.Col(children=[
            #2.1.1
            html.H3(
                'Filters'
            ),
            #2.1.2
            html.H5(
                'From:'
            ),
            #2.1.3
            dcc.DatePickerSingle(
                id='date-picker1',
                min_date_allowed=df['Date'].min(),
                max_date_allowed=df['Date'].max(),
                initial_visible_month=dt(2020, 6, 5),
                date=str(dt(2020, 6, 17, 0, 0, 0))
            ),  # Data Picker
            html.H5(
                'To:'
            ),
            dcc.DatePickerSingle(
                id='date-picker2',
                min_date_allowed=df['Date'].min(),
                max_date_allowed=df['Date'].max(),
                initial_visible_month=dt(2020, 6, 5),
                date=str(dt(2020, 6, 17, 0, 0, 0))
            ),
            #2.1.6
            dcc.RangeSlider(
                id='duration-slider',
                min=0,
                max=df['Duration'].max(),
                step=None,
                marks=durations,

                value=default_duration_slider_val,
                dots=True,

            ),  # Duration Slider

            dcc.RangeSlider(
                id='time-slider',
                min=0,
                max=48,
                step=None,
                marks=times,
                dots=True,
                value=[0, 48],
                pushable=1

            ),  # Time Slider
            html.H5(
                'Condition for Caller/Reciever'
            ),
            #2.1.9
            dcc.Dropdown(
                id='select-caller-receiver',
                options=[{'label': 'Only Caller', 'value': 1}]+[{'label': 'Only Receiver', 'value': 2}]+[
                    {'label': 'Either Caller or Reciever', 'value': 3}]+[{'label': 'Both Caller and Reciever', 'value': 4}],
                value=3,
            ),  # Select if you want the select the numbers to be from Caller/Reciever/Both/Either
           
            html.H5(
                'Select Caller:'
            ),
            dcc.Dropdown(
                id='caller-dropdown',
                options=[{'label': 'None', 'value': 'None'}] + \
                [{'label': k, 'value': k} for k in df['Caller'].unique()],
                value='None',
                multi=True,
            ),  # Dropdown for Caller
            html.H5(
                'Select Reciever:'
            ),
            #2.1.13
            dcc.Dropdown(
                id='receiver-dropdown',
                options=[{'label': 'None', 'value': 'None'}] + \
                [{'label': k, 'value': k} for k in df['Receiver'].unique()],
                value='None',
                multi=True,
            ),  # Dropdown for Reciever,
            html.H5(
                'Find:'
            ),
            dcc.Dropdown(
                id='find-dropdown',
                options=[{'label': 'None', 'value': 'None'}] + \
                [{'label': k, 'value': k} for k in pd.unique(df[['Caller','Receiver']].values.ravel())],
                value='None',
                multi=True,
            ),   # Dropdown for finding,
            #2.1.16
            html.Div([
                dcc.Upload(
                    id='upload-data',
                    children=html.Div([
                        'Drag and Drop or ',
                        html.A('Select a File')
                    ]),
                    style={
                        'width': '100%',
                        'height': '60px',
                        'lineHeight': '60px',
                        'borderWidth': '1px',
                        'borderStyle': 'dashed',
                        'borderRadius': '5px',
                        'textAlign': 'center',
                        'margin-bottom':'12px',
                        'margin-top':'12px'
                    },
                    # Allow multiple files to be uploaded
                    multiple=False
                ),
                html.Div(id='output-data-upload'),
            ])
            ],
            id='filters',lg=3),  # Filters  #Child 2.1 done

        dbc.Col(
           [ html.H3('Network Graph : '),
            dcc.Graph(
                id='network-plot'

            ),
            html.H5('The size of the dots denote the total duration of the caller/callee')],id='plot-area',lg=6),     # Network Plot
        dbc.Col(children=[
            html.H3('Statistics'),
            html.Div([
                dcc.Markdown("""
                **Hover To Get Stats** \n
                Mouse over nodes in the graph to get statistics.
            """),
                html.Pre(id='hover-data',)
            ],),  # Hover Data Container

            html.Div([
                
                dcc.Markdown("""
                **Click to get CDR for a number** \n
                Click on points in the graph to get the call data records.
            """),
                html.Pre(id='click-data', ),
                dcc.Graph(
                    id='pie-chart'
                )
            ], ),  # Click Data Container

            html.Div([
                dcc.Markdown("""
                **Select to see connected people** \n
                Select using rectangle/lasso or by using your mouse.(Use Shift for multiple selections)
            """),
                html.Pre(id='selected-data', ),
            ], )  # Selection Data Container


        ],id='stats',lg=3)

    ],className='container-mid'),
    html.Div(
        id='filtered-data',
        style={'display': 'none'}
    ),
    # Filtered Data
])

#### Callbacks ####
# Callback to update df used for plotting
# Callback to filter dataframe
# REMEMBER WHILE EDITING (RWI): THIS IS A TWO OUTPUT FUNCTION


@app.callback(
    [Output(component_id='filtered-data', component_property='children'),
     Output(component_id='message', component_property='children')],
    [Input('upload-data', 'contents'),Input(component_id='date-picker1', component_property='date'),Input(component_id='date-picker2', component_property='date'), Input(component_id='duration-slider', component_property='value'), Input(component_id='time-slider', component_property='value'),
     Input(component_id='select-caller-receiver', component_property='value'), Input(component_id='caller-dropdown', component_property='value'), Input(component_id='receiver-dropdown', component_property='value')]
)
def update_filtered_div_caller(contents, selected_date1, selected_date2, selected_duration, selected_time, selected_option, selected_caller, selected_receiver):
    # Date,Time,Duration Filter
    if contents is not None:
        content_type, content_string = contents.split(',')
        decoded = base64.b64decode(content_string)
        global df
        df = pd.read_csv(io.StringIO(decoded.decode('utf-8')))
        preprocess_data(df,df2)

    filtered_df = df[(df['Date'] >= pd.to_datetime(selected_date1)) & (df['Date'] <= pd.to_datetime(selected_date2))
                     & ((df['Duration'] >= selected_duration[0]) & (df['Duration'] <= selected_duration[1]))
                     & ((df['Time'] < times[selected_time[1]]['label']) & (df['Time'] >= times[selected_time[0]]['label']))].reset_index(drop=True)

    # Number Filter
    # If Caller is Selected
    if(selected_option == 1):
        if selected_caller != 'None':
            filtered_df = filtered_df[(filtered_df['Caller'].isin(
                list(selected_caller)))].reset_index(drop=True)

   # If Receiver is selected
    if(selected_option == 2):
        if selected_receiver != 'None':
            filtered_df = filtered_df[(filtered_df['Receiver'].isin(
                (selected_receiver)))].reset_index(drop=True)
   # If the option either is selected
    if(selected_option == 3):
        if selected_caller != 'None' or selected_receiver != 'None':
            filtered_df = filtered_df[((filtered_df['Caller'].isin(list(selected_caller))) | (
                filtered_df['Receiver'].isin(list(selected_receiver))))].reset_index(drop=True)
    # If option both is selected
    if(selected_option == 4):
        if selected_caller != 'None' and selected_receiver != 'None':
            filtered_df = df[((filtered_df['Caller'].isin(list(selected_caller))) & (
                filtered_df['Receiver'].isin(list(selected_receiver))))].reset_index(drop=True)
    if filtered_df.shape[0] == 0:
        # No update since nothing matches
        return dash.no_update, 'Nothing Matches that Query'
    else:
        # Update Filtered Dataframe
        return filtered_df.to_json(date_format='iso', orient='split'), 'Updated'
# Callback for hover data
# Display Stats in hoverdata


@app.callback(
    Output('hover-data', 'children'),
    [Input('network-plot', 'hoverData'), Input(component_id='filtered-data', component_property='children')])
def display_hover_data(hoverData, filtered_data):

    df = pd.read_json(filtered_data, orient='split')
    if hoverData is not None:
        # Get node number corresponding to the point.

        nodeNumber = coords_to_node[(
            hoverData['points'][0]['x'], hoverData['points'][0]['y'])]
        hd = 'Selected Number: ' + \
            str(node_to_num[nodeNumber]) + '\n'  # hd: Hover Data string

        # Functions are from stats.py
        hd += "Mean Duration : " + str(meanDur(nodeNumber, df)) + "\n"
        hd += "Peak Hours(duration):\n"
        m = peakHours(nodeNumber, df)
        for x in m:
            hd += "\t\t  " + str(x)+"-"+str(x+1)+" : "+str(m[x])+"\n"
        z = ogIc(nodeNumber, df)  # Outgoing Incoming
        hd += "No. of Outgoing Calls: " + str(z[0])+"\n"
        hd += "No. of Incomming Calls: " + str(z[1])+"\n"
        z = mostCalls(nodeNumber, df)  # Most Calls
        hd += "Most Calls to: " + str(z[0]) + "\n"
        hd += "Most Calls from: " + str(z[1]) + "\n"
        hd += "Most Calls: " + str(z[2]) + "\n"
        return hd
    return "Hover data..."

# Callback for Network Plot
# Show table for the clicked phone number


@app.callback(
    [Output('click-data', 'children'), Output('pie-chart','figure')],
    [Input('network-plot', 'clickData')])
def display_click_data(clickData):
    if clickData is not None:
        nodeNumber = coords_to_node[(
            clickData['points'][0]['x'], clickData['points'][0]['y'])]
        groups=df2[df2['IMEI_node']==nodeNumber].groupby('App_name')['IMEI'].count()
        print(groups,nodeNumber)
        fig = go.Figure(data=dict(type='pie',values=groups,labels=groups.index))
        fig.update_layout(showlegend=False)
        print(fig)
        # Filtering DF
        return df[(df['Caller_node'] == nodeNumber) | (df['Receiver_node'] == nodeNumber)][data_columns].to_string(index=False), fig
    return "Click on a node to view more data", go.Figure()


# Callback for Selected Data
@app.callback(
    Output('selected-data', 'children'),
    [Input('network-plot', 'selectedData'), Input(component_id='filtered-data', component_property='children')])
def display_selected_data(selectedData, filtered_data):
    df = pd.read_json(filtered_data, orient='split')
    # TODO #3 Graph should also be filtered and only nodes in component should be displayed
    if selectedData is not None:
        l = []
        for point in selectedData['points']:
            l.append(node_to_num[coords_to_node[point['x'], point['y']]])
        components = bfs(l, df)
        s = ""
        i = 1
        for component in components:
            if not component:
                continue
            s += "Component "+str(i)+":\n"
            i += 1
            for number in component:
                s += "\t" + str(number) + "\n"
        return s
    return json.dumps(selectedData, indent=2)


# Callback to update network plot
@app.callback(
    Output(component_id='network-plot', component_property='figure'),
    [Input(component_id='filtered-data', component_property='children')]
)
def update_network_plot_caller(filtered_data):
    return plot_network(pd.read_json(filtered_data, orient='split'))

# TODO UPDATE THESE CALLBACKS TO INCLUDE TIME AND DURATION UPDATES
# Callback to change selectors including caller no. according to date


@app.callback(
    Output(component_id='caller-dropdown', component_property='options'),
    [Input(component_id='date-picker1', component_property='date'),Input(component_id='date-picker2', component_property='date')]
)
def update_phone_div_caller(selected_date1, selected_date2):
    return [{'label': 'None', 'value': ''}]+[{'label': k, 'value': k} for k in df[(df['Date'] >= pd.to_datetime(selected_date1)) & (df['Date']<=pd.to_datetime(selected_date2))]['Caller'].unique()]

# Callback to change reciever according  to dates


@app.callback(
    Output(component_id='receiver-dropdown', component_property='options'),
    [Input(component_id='date-picker1', component_property='date'),Input(component_id='date-picker2', component_property='date')]
)
def update_phone_div_receiver(selected_date1, selected_date2):
    return [{'label': 'None', 'value': ''}]+[{'label': k, 'value': k} for k in df[(df['Date'] >= pd.to_datetime(selected_date1)) & (df['Date']<=pd.to_datetime(selected_date2))]['Receiver'].unique()]


@app.callback(
    Output(component_id='find-dropdown', component_property='options'),
    [Input(component_id='date-picker1', component_property='date'),Input(component_id='date-picker2', component_property='date')]
)
def update_phone_div_receiver1(selected_date1, selected_date2):
    return [{'label': 'None', 'value': ''}]+[{'label': k, 'value': k} for k in pd.unique(df[(df['Date'] >= pd.to_datetime(selected_date1)) & (df['Date']<=pd.to_datetime(selected_date2))][['Receiver','Caller']].values.ravel())]


#### Run Server ####
if __name__ == '__main__':
    app.run_server(debug=True, host='0.0.0.0')
