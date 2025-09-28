# # # # # # # import dash
# # # # # # # from dash import dcc, html, Input, Output, State, dash_table, callback_context, ALL
# # # # # # # import dash_bootstrap_components as dbc
# # # # # # # import pandas as pd
# # # # # # # import sqlite3
# # # # # # # import hashlib
# # # # # # # from datetime import datetime
# # # # # # # import base64
# # # # # # # import io
# # # # # # # import random
# # # # # # #
# # # # # # # # Initialize Dash app
# # # # # # # app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP], suppress_callback_exceptions=True)
# # # # # # # app.title = "Capital Pay - Simplified Payment System"
# # # # # # #
# # # # # # #
# # # # # # # # --- Database Setup ---
# # # # # # # def init_db():
# # # # # # #     conn = sqlite3.connect('capital_pay_simplified.db')
# # # # # # #     cursor = conn.cursor()
# # # # # # #
# # # # # # #     # Users table (Admin, Cooperative)
# # # # # # #     cursor.execute('''
# # # # # # #         CREATE TABLE IF NOT EXISTS users (
# # # # # # #             id INTEGER PRIMARY KEY AUTOINCREMENT,
# # # # # # #             username TEXT UNIQUE NOT NULL,
# # # # # # #             password TEXT NOT NULL,
# # # # # # #             role TEXT NOT NULL,
# # # # # # #             cooperative_name TEXT
# # # # # # #         )
# # # # # # #     ''')
# # # # # # #
# # # # # # #     # Submission Batches table
# # # # # # #     cursor.execute('''
# # # # # # #         CREATE TABLE IF NOT EXISTS submission_batches (
# # # # # # #             id INTEGER PRIMARY KEY AUTOINCREMENT,
# # # # # # #             cooperative_id INTEGER,
# # # # # # #             filename TEXT,
# # # # # # #             record_count INTEGER,
# # # # # # #             total_amount REAL,
# # # # # # #             submission_timestamp TIMESTAMP,
# # # # # # #             status TEXT,
# # # # # # #             admin_notes TEXT,
# # # # # # #             FOREIGN KEY (cooperative_id) REFERENCES users (id)
# # # # # # #         )
# # # # # # #     ''')
# # # # # # #
# # # # # # #     # Farmer Payments table
# # # # # # #     cursor.execute('''
# # # # # # #         CREATE TABLE IF NOT EXISTS farmer_payments (
# # # # # # #             id INTEGER PRIMARY KEY AUTOINCREMENT,
# # # # # # #             batch_id INTEGER,
# # # # # # #             farmer_name TEXT NOT NULL,
# # # # # # #             bank_name TEXT NOT NULL,
# # # # # # #             account_number TEXT NOT NULL,
# # # # # # #             amount REAL NOT NULL,
# # # # # # #             status TEXT DEFAULT 'pending',
# # # # # # #             failure_reason TEXT,
# # # # # # #             FOREIGN KEY (batch_id) REFERENCES submission_batches (id)
# # # # # # #         )
# # # # # # #     ''')
# # # # # # #
# # # # # # #     # Payment History table
# # # # # # #     cursor.execute('''
# # # # # # #         CREATE TABLE IF NOT EXISTS payment_history (
# # # # # # #             id INTEGER PRIMARY KEY AUTOINCREMENT,
# # # # # # #             batch_id INTEGER,
# # # # # # #             cooperative_name TEXT,
# # # # # # #             filename TEXT,
# # # # # # #             record_count INTEGER,
# # # # # # #             total_amount REAL,
# # # # # # #             processing_timestamp TIMESTAMP
# # # # # # #         )
# # # # # # #     ''')
# # # # # # #
# # # # # # #     # Pre-populate with default users if table is empty
# # # # # # #     cursor.execute("SELECT COUNT(*) from users")
# # # # # # #     if cursor.fetchone()[0] == 0:
# # # # # # #         admin_password = hashlib.sha256("admin123".encode()).hexdigest()
# # # # # # #         coop_password = hashlib.sha256("coop123".encode()).hexdigest()
# # # # # # #         users_to_add = [
# # # # # # #             ("admin", admin_password, "admin", "Capital Pay Admin"),
# # # # # # #             ("kcu", coop_password, "cooperative", "Kilimanjaro Cooperative Union"),
# # # # # # #             ("mbeyacof", coop_password, "cooperative", "Mbeya Coffee Union"),
# # # # # # #             ("dodoma_coop", coop_password, "cooperative", "Dodoma Grain Cooperative"),
# # # # # # #             ("tanga_coop", coop_password, "cooperative", "Tanga Sisal Cooperative"),
# # # # # # #             ("iringa_coop", coop_password, "cooperative", "Iringa Maize Cooperative"),
# # # # # # #             ("morogoro_coop", coop_password, "cooperative", "Morogoro Rice Cooperative"),
# # # # # # #             ("ruvuma_coop", coop_password, "cooperative", "Ruvuma Cashew Cooperative")
# # # # # # #         ]
# # # # # # #         # Use INSERT OR IGNORE to prevent errors on re-run
# # # # # # #         for user in users_to_add:
# # # # # # #             cursor.execute(
# # # # # # #                 "INSERT OR IGNORE INTO users (username, password, role, cooperative_name) VALUES (?, ?, ?, ?)", user)
# # # # # # #
# # # # # # #     conn.commit()
# # # # # # #     conn.close()
# # # # # # #
# # # # # # #
# # # # # # # # --- Authentication ---
# # # # # # # def authenticate_user(username, password):
# # # # # # #     conn = sqlite3.connect('capital_pay_simplified.db')
# # # # # # #     cursor = conn.cursor()
# # # # # # #     cursor.execute("SELECT id, password, role, cooperative_name FROM users WHERE username = ?", (username,))
# # # # # # #     user = cursor.fetchone()
# # # # # # #     conn.close()
# # # # # # #
# # # # # # #     if user and user[1] == hashlib.sha256(password.encode()).hexdigest():
# # # # # # #         return {"id": user[0], "username": username, "role": user[2], "cooperative_name": user[3]}
# # # # # # #     return None
# # # # # # #
# # # # # # #
# # # # # # # # --- Layout Definitions ---
# # # # # # # def create_login_layout():
# # # # # # #     return dbc.Container([
# # # # # # #         dbc.Row(dbc.Col(dbc.Card([
# # # # # # #             dbc.CardBody([
# # # # # # #                 html.H2("Capital Pay", className="text-center mb-4 text-success"),
# # # # # # #                 dbc.Input(id="login-username", placeholder="Username", type="text", className="mb-3"),
# # # # # # #                 dbc.Input(id="login-password", placeholder="Password", type="password", className="mb-3"),
# # # # # # #                 dbc.Button("Login", id="login-button", color="success", className="w-100"),
# # # # # # #                 html.Div(id="login-alert-placeholder", className="mt-3")
# # # # # # #             ])
# # # # # # #         ], className="shadow"), width=10, sm=8, md=6, lg=4), justify="center",
# # # # # # #             className="min-vh-100 align-items-center"),
# # # # # # #
# # # # # # #         dbc.Alert([
# # # # # # #             html.H5("Demo Credentials", className="alert-heading"),
# # # # # # #             html.P("Use the following details to log in:"),
# # # # # # #             html.Hr(),
# # # # # # #             html.P([html.B("Admin: "), "username: ", html.Code("admin"), ", password: ", html.Code("admin123")]),
# # # # # # #             html.P([html.B("Cooperative Usernames: "), html.Code("kcu"), ", ", html.Code("mbeyacof"), ", ",
# # # # # # #                     html.Code("dodoma_coop")]),
# # # # # # #             html.P([html.B("Cooperative Password: "), "all use ", html.Code("coop123")]),
# # # # # # #         ], color="info",
# # # # # # #             style={"position": "absolute", "bottom": "10px", "left": "10px", "width": "auto", "maxWidth": "550px"})
# # # # # # #     ], fluid=True, className="bg-light")
# # # # # # #
# # # # # # #
# # # # # # # def create_cooperative_layout(session_data):
# # # # # # #     return html.Div([
# # # # # # #         dbc.NavbarSimple(brand=session_data.get('cooperative_name'),
# # # # # # #                          children=[dbc.Button("Logout", id="logout-button", color="light", outline=True)],
# # # # # # #                          color="success", dark=True),
# # # # # # #         dbc.Container([
# # # # # # #             dbc.Alert(id="coop-alert", is_open=False, duration=4000),
# # # # # # #             html.H3("Co-operatives Farmer Data Submission  Portal", className="my-4"),
# # # # # # #             dcc.Upload(
# # # # # # #                 id='upload-data',
# # # # # # #                 children=html.Div(['Drag and Drop or ', html.A('Select a CSV/Excel File')]),
# # # # # # #                 style={'width': '100%', 'height': '60px', 'lineHeight': '60px', 'borderWidth': '1px',
# # # # # # #                        'borderStyle': 'dashed', 'borderRadius': '5px', 'textAlign': 'center', 'margin': '10px 0'},
# # # # # # #                 multiple=False
# # # # # # #             ),
# # # # # # #             html.Hr(),
# # # # # # #             html.Div(id="submission-table-placeholder"),
# # # # # # #             html.Hr(),
# # # # # # #             html.H3("Submission History", className="my-4"),
# # # # # # #             html.Div(id="coop-history-placeholder"),
# # # # # # #         ], fluid=True),
# # # # # # #         dbc.Modal(id="coop-results-modal", size="xl", is_open=False)
# # # # # # #     ])
# # # # # # #
# # # # # # #
# # # # # # # def create_admin_layout(session_data):
# # # # # # #     return html.Div([
# # # # # # #         dbc.Toast(
# # # # # # #             id="ipn-toast",
# # # # # # #             is_open=False,
# # # # # # #             duration=6000,
# # # # # # #             icon="success",
# # # # # # #             style={"position": "fixed", "top": 20, "right": 20, "width": 350, "zIndex": 9999}
# # # # # # #         ),
# # # # # # #         dbc.NavbarSimple(brand="Union Admin Payments Dashboard",
# # # # # # #                          children=[dbc.Button("Logout", id="logout-button", color="light", outline=True)],
# # # # # # #                          color="primary", dark=True),
# # # # # # #         dbc.Container([
# # # # # # #             html.Div(id="admin-dashboard-content"),
# # # # # # #             html.Hr(),
# # # # # # #             html.H3("Payment History", className="my-4"),
# # # # # # #             dbc.Button("Show/Hide History", id="toggle-history-btn", className="mb-3"),
# # # # # # #             dbc.Collapse(
# # # # # # #                 html.Div(id="payment-history-placeholder"),
# # # # # # #                 id="history-collapse",
# # # # # # #                 is_open=False
# # # # # # #             )
# # # # # # #         ], fluid=True, className="py-4"),
# # # # # # #         dbc.Modal(id="details-modal", size="xl", is_open=False),
# # # # # # #         dbc.Modal([
# # # # # # #             dbc.ModalHeader("Processing Payment"),
# # # # # # #             dbc.ModalBody(id="payment-animation-placeholder"),
# # # # # # #             dbc.ModalFooter(dbc.Button("Close", id="payment-close-button", color="secondary", disabled=True))
# # # # # # #         ], id="payment-modal", backdrop="static")
# # # # # # #     ])
# # # # # # #
# # # # # # #
# # # # # # # # Main App Layout
# # # # # # # app.layout = html.Div([
# # # # # # #     dcc.Store(id="user-session", storage_type="session"),
# # # # # # #     dcc.Store(id="batch-to-process"),
# # # # # # #     dcc.Store(id='ipn-data-store'),
# # # # # # #     dcc.Interval(id='payment-interval', interval=2000, n_intervals=0, disabled=True),
# # # # # # #     html.Div(id="main-content")
# # # # # # # ])
# # # # # # #
# # # # # # #
# # # # # # # # --- Callbacks ---
# # # # # # #
# # # # # # # # 1. Main Router
# # # # # # # @app.callback(Output("main-content", "children"), Input("user-session", "data"))
# # # # # # # def display_page(session_data):
# # # # # # #     if session_data:
# # # # # # #         if session_data.get("role") == "admin":
# # # # # # #             return create_admin_layout(session_data)
# # # # # # #         elif session_data.get("role") == "cooperative":
# # # # # # #             return create_cooperative_layout(session_data)
# # # # # # #     return create_login_layout()
# # # # # # #
# # # # # # #
# # # # # # # # 2. Login
# # # # # # # @app.callback(
# # # # # # #     Output("user-session", "data"),
# # # # # # #     Output("login-alert-placeholder", "children"),
# # # # # # #     Input("login-button", "n_clicks"),
# # # # # # #     State("login-username", "value"),
# # # # # # #     State("login-password", "value"),
# # # # # # #     prevent_initial_call=True
# # # # # # # )
# # # # # # # def handle_login(n_clicks, username, password):
# # # # # # #     if not n_clicks:
# # # # # # #         return dash.no_update, dash.no_update
# # # # # # #
# # # # # # #     if not username or not password:
# # # # # # #         return dash.no_update, dbc.Alert("Fields cannot be empty.", color="warning")
# # # # # # #
# # # # # # #     user = authenticate_user(username, password)
# # # # # # #     if user:
# # # # # # #         return user, None
# # # # # # #
# # # # # # #     return None, dbc.Alert("Invalid credentials.", color="danger")
# # # # # # #
# # # # # # #
# # # # # # # # 3. Logout
# # # # # # # @app.callback(
# # # # # # #     Output("user-session", "data", allow_duplicate=True),
# # # # # # #     Input("logout-button", "n_clicks"),
# # # # # # #     prevent_initial_call=True,
# # # # # # # )
# # # # # # # def handle_logout(n_clicks):
# # # # # # #     if n_clicks:
# # # # # # #         return None
# # # # # # #     return dash.no_update
# # # # # # #
# # # # # # #
# # # # # # # # 4. Cooperative: File Upload and Display
# # # # # # # @app.callback(
# # # # # # #     Output("submission-table-placeholder", "children"),
# # # # # # #     Input('upload-data', 'contents'),
# # # # # # #     State('upload-data', 'filename'),
# # # # # # #     prevent_initial_call=True,
# # # # # # # )
# # # # # # # def update_output(contents, filename):
# # # # # # #     if contents is None: return html.Div()
# # # # # # #
# # # # # # #     content_type, content_string = contents.split(',')
# # # # # # #     decoded = base64.b64decode(content_string)
# # # # # # #     try:
# # # # # # #         df = pd.read_csv(io.StringIO(decoded.decode('utf-8'))) if 'csv' in filename else pd.read_excel(
# # # # # # #             io.BytesIO(decoded))
# # # # # # #         required_cols = {'farmer_name', 'bank_name', 'account_number', 'amount'}
# # # # # # #         if not required_cols.issubset(df.columns):
# # # # # # #             return dbc.Alert(f"File is missing columns: {required_cols - set(df.columns)}", color="danger")
# # # # # # #
# # # # # # #         return html.Div([
# # # # # # #             dcc.Store(id='submission-data', data={'df': df.to_dict('records'), 'filename': filename}),
# # # # # # #             dbc.Alert(id="save-changes-alert", is_open=False, duration=3000, color="success"),
# # # # # # #             html.H5("Review and Edit Data"),
# # # # # # #             dash_table.DataTable(id='editable-datatable', data=df.to_dict('records'),
# # # # # # #                                  columns=[{'name': i, 'id': i} for i in df.columns], page_size=10,
# # # # # # #                                  style_table={'overflowX': 'auto'}, editable=True),
# # # # # # #             html.Div([
# # # # # # #                 dbc.Button("Save Changes", id="save-edited-data-button", color="info", className="mt-3"),
# # # # # # #                 dbc.Button("Submit to Admin", id="submit-to-admin-button", color="primary", className="mt-3"),
# # # # # # #             ], className="d-flex justify-content-end gap-2")
# # # # # # #         ])
# # # # # # #     except Exception as e:
# # # # # # #         return dbc.Alert(f"There was an error processing the file: {e}", color="danger")
# # # # # # #
# # # # # # #
# # # # # # # # 5. Cooperative: Save and Submit
# # # # # # # @app.callback(
# # # # # # #     Output("save-changes-alert", "is_open"), Output("save-changes-alert", "children"),
# # # # # # #     Output("submission-data", "data", allow_duplicate=True),
# # # # # # #     Input("save-edited-data-button", "n_clicks"),
# # # # # # #     State("editable-datatable", "data"), State("submission-data", "data"),
# # # # # # #     prevent_initial_call=True
# # # # # # # )
# # # # # # # def save_edits_to_store(n_clicks, table_data, original_submission_data):
# # # # # # #     if not n_clicks: return False, "", dash.no_update
# # # # # # #     updated_submission_data = {'df': table_data, 'filename': original_submission_data['filename']}
# # # # # # #     return True, "Your changes have been saved!", updated_submission_data
# # # # # # #
# # # # # # #
# # # # # # # @app.callback(
# # # # # # #     Output("coop-alert", "children"), Output("coop-alert", "is_open"), Output("coop-alert", "color"),
# # # # # # #     Input("submit-to-admin-button", "n_clicks"),
# # # # # # #     State("submission-data", "data"), State("user-session", "data"),
# # # # # # #     prevent_initial_call=True,
# # # # # # # )
# # # # # # # def submit_to_admin(n_clicks, submission_data, session_data):
# # # # # # #     if not n_clicks or not submission_data: return "", False, ""
# # # # # # #     df = pd.DataFrame(submission_data.get('df'))
# # # # # # #     conn = sqlite3.connect('capital_pay_simplified.db')
# # # # # # #     cursor = conn.cursor()
# # # # # # #     try:
# # # # # # #         cursor.execute(
# # # # # # #             "INSERT INTO submission_batches (cooperative_id, filename, record_count, total_amount, submission_timestamp, status) VALUES (?, ?, ?, ?, ?, ?)",
# # # # # # #             (session_data['id'], submission_data.get('filename'), len(df), df['amount'].sum(), datetime.now(),
# # # # # # #              'pending_approval'))
# # # # # # #         batch_id = cursor.lastrowid
# # # # # # #         df_to_db = df[['farmer_name', 'bank_name', 'account_number', 'amount']]
# # # # # # #         df_to_db['batch_id'] = batch_id
# # # # # # #         df_to_db.to_sql('farmer_payments', conn, if_exists='append', index=False)
# # # # # # #         conn.commit()
# # # # # # #         msg, color = f"Successfully submitted {len(df)} records.", "success"
# # # # # # #     except Exception as e:
# # # # # # #         conn.rollback()
# # # # # # #         msg, color = f"Database error: {e}", "danger"
# # # # # # #     finally:
# # # # # # #         conn.close()
# # # # # # #     return msg, True, color
# # # # # # #
# # # # # # #
# # # # # # # # 6. Admin: Render Dashboard
# # # # # # # @app.callback(
# # # # # # #     Output("admin-dashboard-content", "children"),
# # # # # # #     Input("user-session", "data"), Input("payment-close-button", "n_clicks")
# # # # # # # )
# # # # # # # def render_admin_dashboard(session_data, n_clicks):
# # # # # # #     if not session_data or session_data.get("role") != "admin": return None
# # # # # # #     conn = sqlite3.connect('capital_pay_simplified.db')
# # # # # # #     query = "SELECT b.id, u.cooperative_name, b.filename, b.record_count, b.total_amount, b.submission_timestamp FROM submission_batches b JOIN users u ON b.cooperative_id = u.id WHERE b.status = 'pending_approval' ORDER BY b.submission_timestamp DESC"
# # # # # # #     batches_df = pd.read_sql_query(query, conn)
# # # # # # #     conn.close()
# # # # # # #     if batches_df.empty: return dbc.Alert("No Pending Payments found.", color="info", className="m-4")
# # # # # # #     cards = [
# # # # # # #         dbc.Card([
# # # # # # #             dbc.CardHeader(f"From: {row['cooperative_name']}"),
# # # # # # #             dbc.CardBody([
# # # # # # #                 html.H5(row['filename'], className="card-title"),
# # # # # # #                 html.P(f"{row['record_count']} farmers, Total Amount: TSH {row['total_amount']:,.2f}"),
# # # # # # #                 html.Small(
# # # # # # #                     f"Submitted: {datetime.strptime(row['submission_timestamp'].split('.')[0], '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d %I:%M %p')}",
# # # # # # #                     className="text-muted"),
# # # # # # #             ]),
# # # # # # #             dbc.CardFooter(html.Div([
# # # # # # #                 dbc.Button("View Details", id={'type': 'view-details-btn', 'index': row['id']}, color="secondary"),
# # # # # # #                 dbc.Button("Pay Now", id={'type': 'pay-now-btn', 'index': row['id']}, color="success"),
# # # # # # #             ], className="d-flex justify-content-between"))
# # # # # # #         ], className="mb-3") for _, row in batches_df.iterrows()
# # # # # # #     ]
# # # # # # #     return [html.H3("Pending Payments", className="mb-4")] + cards
# # # # # # #
# # # # # # #
# # # # # # # # 7. Admin: View Details Modal and Save Notes
# # # # # # # @app.callback(
# # # # # # #     Output("details-modal", "is_open"), Output("details-modal", "children"),
# # # # # # #     Input({'type': 'view-details-btn', 'index': ALL}, 'n_clicks'),
# # # # # # #     prevent_initial_call=True
# # # # # # # )
# # # # # # # def toggle_details_modal(n_clicks):
# # # # # # #     if not any(n_clicks): return False, None
# # # # # # #     batch_id = int(eval(callback_context.triggered[0]['prop_id'].split('.')[0])['index'])
# # # # # # #     conn = sqlite3.connect('capital_pay_simplified.db')
# # # # # # #     df = pd.read_sql_query(
# # # # # # #         "SELECT farmer_name, bank_name, account_number, amount FROM farmer_payments WHERE batch_id = ?", conn,
# # # # # # #         params=(batch_id,))
# # # # # # #     note_df = pd.read_sql_query("SELECT admin_notes FROM submission_batches WHERE id = ?", conn, params=(batch_id,))
# # # # # # #     conn.close()
# # # # # # #
# # # # # # #     current_note = note_df['admin_notes'].iloc[0] or ""
# # # # # # #
# # # # # # #     return True, [
# # # # # # #         dbc.ModalHeader(f"Submission Details (Batch ID: {batch_id})"),
# # # # # # #         dbc.ModalBody([
# # # # # # #             dash_table.DataTable(data=df.to_dict('records'), columns=[{'name': i, 'id': i} for i in df.columns],
# # # # # # #                                  style_table={'overflowX': 'auto', 'maxHeight': '40vh', 'overflowY': 'auto'},
# # # # # # #                                  editable=True, style_data_conditional=[
# # # # # # #                     {'if': {'filter_query': '{amount} > 400000'}, 'backgroundColor': '#d4edda', 'color': '#155724'},
# # # # # # #                     {'if': {'filter_query': '{amount} < 100000'}, 'backgroundColor': '#fff3cd', 'color': '#856404'}]),
# # # # # # #             html.Hr(),
# # # # # # #             html.H5("Admin Notes for Cooperative"),
# # # # # # #             dbc.Alert(id="note-save-alert", is_open=False, duration=3000),
# # # # # # #             dcc.Textarea(id={'type': 'admin-note-textarea', 'index': batch_id}, value=current_note,
# # # # # # #                          style={'width': '100%', 'height': 100}),
# # # # # # #             dbc.Button("Save Note", id={'type': 'save-note-btn', 'index': batch_id}, color="primary", className="mt-2")
# # # # # # #         ])
# # # # # # #     ]
# # # # # # #
# # # # # # #
# # # # # # # @app.callback(
# # # # # # #     Output("note-save-alert", "is_open"), Output("note-save-alert", "children"), Output("note-save-alert", "color"),
# # # # # # #     Input({'type': 'save-note-btn', 'index': ALL}, 'n_clicks'),
# # # # # # #     State({'type': 'admin-note-textarea', 'index': ALL}, 'value'),
# # # # # # #     prevent_initial_call=True
# # # # # # # )
# # # # # # # def save_admin_note(n_clicks, notes):
# # # # # # #     if not any(n_clicks): return False, "", ""
# # # # # # #
# # # # # # #     ctx = callback_context.triggered[0]
# # # # # # #     batch_id = int(eval(ctx['prop_id'].split('.')[0])['index'])
# # # # # # #     note_value = notes[0]  # Since we only have one textarea visible at a time
# # # # # # #
# # # # # # #     try:
# # # # # # #         conn = sqlite3.connect('capital_pay_simplified.db')
# # # # # # #         cursor = conn.cursor()
# # # # # # #         cursor.execute("UPDATE submission_batches SET admin_notes = ? WHERE id = ?", (note_value, batch_id))
# # # # # # #         conn.commit()
# # # # # # #         conn.close()
# # # # # # #         return True, "Note saved successfully!", "success"
# # # # # # #     except Exception as e:
# # # # # # #         return True, f"Error saving note: {e}", "danger"
# # # # # # #
# # # # # # #
# # # # # # # # 8. Admin: Payment Processing
# # # # # # # PAYMENT_STEPS = ["Initiating Capital Pay secure engine...", "Pre-processing and validating farmer data...",
# # # # # # #                  "Connecting to inter-bank payment gateway...", "Securely settling respective farmers' accounts...",
# # # # # # #                  "Transactions successful! Finalizing report..."]
# # # # # # #
# # # # # # #
# # # # # # # @app.callback(
# # # # # # #     Output("payment-modal", "is_open"), Output("payment-interval", "disabled"),
# # # # # # #     Output("payment-animation-placeholder", "children"), Output("payment-close-button", "disabled"),
# # # # # # #     Output("batch-to-process", "data"), Output("ipn-data-store", "data"),
# # # # # # #     Input({'type': 'pay-now-btn', 'index': ALL}, 'n_clicks'),
# # # # # # #     Input("payment-interval", "n_intervals"), Input("payment-close-button", "n_clicks"),
# # # # # # #     State("batch-to-process", "data"),
# # # # # # #     prevent_initial_call=True
# # # # # # # )
# # # # # # # def handle_payment_processing(pay_clicks, n_intervals, close_clicks, batch_id):
# # # # # # #     if not callback_context.triggered: return dash.no_update
# # # # # # #
# # # # # # #     triggered_id = callback_context.triggered_id
# # # # # # #     if triggered_id and isinstance(triggered_id, dict) and triggered_id.get("type") == "pay-now-btn" and any(
# # # # # # #             pay_clicks):
# # # # # # #         new_batch_id = int(triggered_id['index'])
# # # # # # #         animation_step = html.Div([html.Div("🔄", style={'fontSize': 50, 'textAlign': 'center'}),
# # # # # # #                                    dbc.Progress(value=5, className="mb-2", striped=True, animated=True),
# # # # # # #                                    html.P(PAYMENT_STEPS[0], className="text-center")])
# # # # # # #         return True, False, animation_step, True, new_batch_id, dash.no_update
# # # # # # #
# # # # # # #     if triggered_id == 'payment-interval' and batch_id is not None:
# # # # # # #         step_index = n_intervals
# # # # # # #         if step_index < len(PAYMENT_STEPS):
# # # # # # #             progress = int(((step_index + 1) / len(PAYMENT_STEPS)) * 100)
# # # # # # #             animation_step = html.Div([html.Div("🔄", style={'fontSize': 50, 'textAlign': 'center'}),
# # # # # # #                                        dbc.Progress(value=progress, className="mb-2", striped=True, animated=True,
# # # # # # #                                                     style={"height": "20px"}),
# # # # # # #                                        html.P(PAYMENT_STEPS[step_index], className="text-center")])
# # # # # # #             return True, False, animation_step, True, batch_id, dash.no_update
# # # # # # #         else:
# # # # # # #             conn = sqlite3.connect('capital_pay_simplified.db')
# # # # # # #             cursor = conn.cursor()
# # # # # # #             cursor.execute(
# # # # # # #                 "SELECT u.cooperative_name, b.record_count FROM submission_batches b JOIN users u ON b.cooperative_id = u.id WHERE b.id = ?",
# # # # # # #                 (batch_id,))
# # # # # # #             batch_info = cursor.fetchone()
# # # # # # #             cursor.execute("UPDATE submission_batches SET status = 'processed' WHERE id = ?", (batch_id,))
# # # # # # #
# # # # # # #             payments_to_update, success_count, failed_count = [], 0, 0
# # # # # # #             failure_reasons = ["Invalid Account Number", "Bank Network Error", "Account Closed", "Name Mismatch"]
# # # # # # #             cursor.execute("SELECT id FROM farmer_payments WHERE batch_id = ?", (batch_id,))
# # # # # # #             for (pid,) in cursor.fetchall():
# # # # # # #                 if random.random() < 0.9:
# # # # # # #                     payments_to_update.append(('paid', None, pid));
# # # # # # #                     success_count += 1
# # # # # # #                 else:
# # # # # # #                     payments_to_update.append(('failed', random.choice(failure_reasons), pid));
# # # # # # #                     failed_count += 1
# # # # # # #             cursor.executemany("UPDATE farmer_payments SET status = ?, failure_reason = ? WHERE id = ?",
# # # # # # #                                payments_to_update)
# # # # # # #
# # # # # # #             conn.commit()
# # # # # # #             conn.close()
# # # # # # #
# # # # # # #             ipn_data = {'coop_name': batch_info[0], 'success': success_count, 'failed': failed_count,
# # # # # # #                         'total': batch_info[1]}
# # # # # # #             result = html.Div([html.Div("✅", style={'fontSize': 60, 'textAlign': 'center', 'color': 'green'}),
# # # # # # #                                dbc.Progress(value=100, color="success", className="mb-2"),
# # # # # # #                                html.H5("Payment Processed!", className="text-success text-center")])
# # # # # # #             return True, True, result, False, None, ipn_data
# # # # # # #
# # # # # # #     if triggered_id == 'payment-close-button':
# # # # # # #         return False, True, "", True, None, None
# # # # # # #
# # # # # # #     return dash.no_update
# # # # # # #
# # # # # # #
# # # # # # # # 9. IPN Toast Notification
# # # # # # # @app.callback(
# # # # # # #     Output("ipn-toast", "is_open"), Output("ipn-toast", "header"),
# # # # # # #     Output("ipn-toast", "children"), Output("ipn-toast", "icon"),
# # # # # # #     Input("ipn-data-store", "data"),
# # # # # # #     prevent_initial_call=True
# # # # # # # )
# # # # # # # def show_ipn_toast(data):
# # # # # # #     if not data: return False, "", "", ""
# # # # # # #     header = "IPN: Transaction Complete"
# # # # # # #     icon = "success" if data['failed'] == 0 else "warning"
# # # # # # #     body = f"{data['coop_name']}: Paid {data['success']}/{data['total']} farmers. ({data['failed']} failed)"
# # # # # # #     return True, header, body, icon
# # # # # # #
# # # # # # #
# # # # # # # # 10. Cooperative History and Results
# # # # # # # @app.callback(
# # # # # # #     Output("coop-history-placeholder", "children"),
# # # # # # #     Input("user-session", "data"), Input("coop-alert", "is_open"),
# # # # # # #     State("user-session", "data")
# # # # # # # )
# # # # # # # def render_coop_history(session, alert_is_open, session_data):
# # # # # # #     if not session_data: return None
# # # # # # #     conn = sqlite3.connect('capital_pay_simplified.db')
# # # # # # #     df = pd.read_sql_query(
# # # # # # #         "SELECT id, filename, status, submission_timestamp, admin_notes FROM submission_batches WHERE cooperative_id = ? ORDER BY submission_timestamp DESC",
# # # # # # #         conn, params=(session_data['id'],))
# # # # # # #     conn.close()
# # # # # # #     if df.empty: return dbc.Alert("No submissions yet.", color="info")
# # # # # # #
# # # # # # #     return dbc.Accordion([
# # # # # # #         dbc.AccordionItem([
# # # # # # #             html.P(
# # # # # # #                 f"Submitted on: {datetime.strptime(row['submission_timestamp'].split('.')[0], '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d %I:%M %p')}"),
# # # # # # #             dbc.Alert(f"Admin Note: {row['admin_notes']}", color="info") if row['admin_notes'] else "",
# # # # # # #             dbc.Button("View Results", id={'type': 'view-results-btn', 'index': row['id']}, color="info", size="sm") if
# # # # # # #             row['status'] == 'processed' else ""
# # # # # # #         ], title=html.Div([row['filename'], dbc.Badge(row['status'].replace('_', ' ').title(),
# # # # # # #                                                       color="success" if row['status'] == 'processed' else "warning",
# # # # # # #                                                       className="ms-2")]))
# # # # # # #         for _, row in df.iterrows()
# # # # # # #     ], start_collapsed=True)
# # # # # # #
# # # # # # #
# # # # # # # @app.callback(
# # # # # # #     Output('coop-results-modal', 'is_open'), Output('coop-results-modal', 'children'),
# # # # # # #     Input({'type': 'view-results-btn', 'index': ALL}, 'n_clicks'),
# # # # # # #     prevent_initial_call=True
# # # # # # # )
# # # # # # # def show_coop_results_modal(n_clicks):
# # # # # # #     if not any(n_clicks): return False, None
# # # # # # #     batch_id = int(eval(callback_context.triggered[0]['prop_id'].split('.')[0])['index'])
# # # # # # #     conn = sqlite3.connect('capital_pay_simplified.db')
# # # # # # #     df = pd.read_sql_query(
# # # # # # #         "SELECT farmer_name, bank_name, account_number, amount, status, failure_reason FROM farmer_payments WHERE batch_id = ?",
# # # # # # #         conn, params=(batch_id,))
# # # # # # #     conn.close()
# # # # # # #     return True, [
# # # # # # #         dbc.ModalHeader(f"Payment Results (Batch ID: {batch_id})"),
# # # # # # #         dbc.ModalBody(dash_table.DataTable(
# # # # # # #             data=df.to_dict('records'),
# # # # # # #             columns=[{'name': i.replace('_', ' ').title(), 'id': i} for i in df.columns],
# # # # # # #             style_table={'overflowX': 'auto'}, editable=True,
# # # # # # #             style_data_conditional=[
# # # # # # #                 {'if': {'filter_query': '{status} = "paid"'}, 'backgroundColor': '#d4edda', 'color': '#155724'},
# # # # # # #                 {'if': {'filter_query': '{status} = "failed"'}, 'backgroundColor': '#f8d7da', 'color': '#721c24'}
# # # # # # #             ]
# # # # # # #         ))
# # # # # # #     ]
# # # # # # #
# # # # # # #
# # # # # # # # 11. Admin: Payment History
# # # # # # # @app.callback(
# # # # # # #     Output("history-collapse", "is_open"),
# # # # # # #     Input("toggle-history-btn", "n_clicks"), State("history-collapse", "is_open"),
# # # # # # #     prevent_initial_call=True
# # # # # # # )
# # # # # # # def toggle_history_collapse(n, is_open):
# # # # # # #     if n: return not is_open
# # # # # # #     return is_open
# # # # # # #
# # # # # # #
# # # # # # # @app.callback(
# # # # # # #     Output("payment-history-placeholder", "children"),
# # # # # # #     Input("history-collapse", "is_open"),
# # # # # # #     prevent_initial_call=True
# # # # # # # )
# # # # # # # def render_payment_history(is_open):
# # # # # # #     if not is_open: return dash.no_update
# # # # # # #     conn = sqlite3.connect('capital_pay_simplified.db')
# # # # # # #     history_df = pd.read_sql_query("SELECT * FROM payment_history ORDER BY processing_timestamp DESC", conn)
# # # # # # #     conn.close()
# # # # # # #     if history_df.empty: return dbc.Alert("No processed payments found.", color="secondary")
# # # # # # #     return dash_table.DataTable(data=history_df.to_dict('records'),
# # # # # # #                                 columns=[{'name': i.replace('_', ' ').title(), 'id': i} for i in history_df.columns],
# # # # # # #                                 page_size=20, style_table={'overflowX': 'auto'}, editable=True)
# # # # # # #
# # # # # # #
# # # # # # # # --- Run Application ---
# # # # # # # if __name__ == "__main__":
# # # # # # #     init_db()
# # # # # # #     app.run(debug=True, port=8055)
# # # # # # #
# # # # # #
# # # # # #
# # # # # # import dash
# # # # # # from dash import dcc, html, Input, Output, State, dash_table, callback_context, ALL
# # # # # # import dash_bootstrap_components as dbc
# # # # # # import pandas as pd
# # # # # # import sqlite3
# # # # # # import hashlib
# # # # # # from datetime import datetime
# # # # # # import base64
# # # # # # import io
# # # # # # import random
# # # # # #
# # # # # # # Initialize Dash app
# # # # # # app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP], suppress_callback_exceptions=True)
# # # # # # app.title = "Capital Pay - Simplified Payment System"
# # # # # #
# # # # # #
# # # # # # # --- Database Setup ---
# # # # # # def init_db():
# # # # # #     conn = sqlite3.connect('capital_pay_simplified.db')
# # # # # #     cursor = conn.cursor()
# # # # # #
# # # # # #     # Users table (Admin, Cooperative)
# # # # # #     cursor.execute('''
# # # # # #         CREATE TABLE IF NOT EXISTS users (
# # # # # #             id INTEGER PRIMARY KEY AUTOINCREMENT,
# # # # # #             username TEXT UNIQUE NOT NULL,
# # # # # #             password TEXT NOT NULL,
# # # # # #             role TEXT NOT NULL,
# # # # # #             cooperative_name TEXT
# # # # # #         )
# # # # # #     ''')
# # # # # #
# # # # # #     # Submission Batches table
# # # # # #     cursor.execute('''
# # # # # #         CREATE TABLE IF NOT EXISTS submission_batches (
# # # # # #             id INTEGER PRIMARY KEY AUTOINCREMENT,
# # # # # #             cooperative_id INTEGER,
# # # # # #             filename TEXT,
# # # # # #             record_count INTEGER,
# # # # # #             total_amount REAL,
# # # # # #             submission_timestamp TIMESTAMP,
# # # # # #             status TEXT,
# # # # # #             admin_notes TEXT,
# # # # # #             FOREIGN KEY (cooperative_id) REFERENCES users (id)
# # # # # #         )
# # # # # #     ''')
# # # # # #
# # # # # #     # Farmer Payments table
# # # # # #     cursor.execute('''
# # # # # #         CREATE TABLE IF NOT EXISTS farmer_payments (
# # # # # #             id INTEGER PRIMARY KEY AUTOINCREMENT,
# # # # # #             batch_id INTEGER,
# # # # # #             farmer_name TEXT NOT NULL,
# # # # # #             bank_name TEXT NOT NULL,
# # # # # #             account_number TEXT NOT NULL,
# # # # # #             amount REAL NOT NULL,
# # # # # #             status TEXT DEFAULT 'pending',
# # # # # #             failure_reason TEXT,
# # # # # #             FOREIGN KEY (batch_id) REFERENCES submission_batches (id)
# # # # # #         )
# # # # # #     ''')
# # # # # #
# # # # # #     # Payment History table
# # # # # #     # This schema now includes cooperative_id, which caused the error with the old DB file.
# # # # # #     cursor.execute('''
# # # # # #         CREATE TABLE IF NOT EXISTS payment_history (
# # # # # #             id INTEGER PRIMARY KEY AUTOINCREMENT,
# # # # # #             batch_id INTEGER,
# # # # # #             cooperative_id INTEGER,
# # # # # #             cooperative_name TEXT,
# # # # # #             filename TEXT,
# # # # # #             record_count INTEGER,
# # # # # #             total_amount REAL,
# # # # # #             processing_timestamp TIMESTAMP,
# # # # # #             FOREIGN KEY (cooperative_id) REFERENCES users (id)
# # # # # #         )
# # # # # #     ''')
# # # # # #
# # # # # #
# # # # # #     # Pre-populate with default users if table is empty
# # # # # #     cursor.execute("SELECT COUNT(*) from users")
# # # # # #     if cursor.fetchone()[0] == 0:
# # # # # #         admin_password = hashlib.sha256("admin123".encode()).hexdigest()
# # # # # #         coop_password = hashlib.sha256("coop123".encode()).hexdigest()
# # # # # #         users_to_add = [
# # # # # #             ("admin", admin_password, "admin", "Capital Pay Admin"),
# # # # # #             ("kcu", coop_password, "cooperative", "Kilimanjaro Cooperative Union"),
# # # # # #             ("mbeyacof", coop_password, "cooperative", "Mbeya Coffee Union"),
# # # # # #             ("dodoma_coop", coop_password, "cooperative", "Dodoma Grain Cooperative"),
# # # # # #             ("tanga_coop", coop_password, "cooperative", "Tanga Sisal Cooperative"),
# # # # # #             ("iringa_coop", coop_password, "cooperative", "Iringa Maize Cooperative"),
# # # # # #             ("morogoro_coop", coop_password, "cooperative", "Morogoro Rice Cooperative"),
# # # # # #             ("ruvuma_coop", coop_password, "cooperative", "Ruvuma Cashew Cooperative")
# # # # # #         ]
# # # # # #         for user in users_to_add:
# # # # # #             cursor.execute(
# # # # # #                 "INSERT OR IGNORE INTO users (username, password, role, cooperative_name) VALUES (?, ?, ?, ?)", user)
# # # # # #
# # # # # #     conn.commit()
# # # # # #     conn.close()
# # # # # #
# # # # # #
# # # # # # # --- Authentication ---
# # # # # # def authenticate_user(username, password):
# # # # # #     conn = sqlite3.connect('capital_pay_simplified.db')
# # # # # #     cursor = conn.cursor()
# # # # # #     cursor.execute("SELECT id, password, role, cooperative_name FROM users WHERE username = ?", (username,))
# # # # # #     user = cursor.fetchone()
# # # # # #     conn.close()
# # # # # #
# # # # # #     if user and user[1] == hashlib.sha256(password.encode()).hexdigest():
# # # # # #         return {"id": user[0], "username": username, "role": user[2], "cooperative_name": user[3]}
# # # # # #     return None
# # # # # #
# # # # # #
# # # # # # # --- Layout Definitions ---
# # # # # # def create_login_layout():
# # # # # #     return dbc.Container([
# # # # # #         dbc.Row(dbc.Col(dbc.Card([
# # # # # #             dbc.CardBody([
# # # # # #                 html.H2("Capital Pay", className="text-center mb-4 text-success"),
# # # # # #                 dbc.Input(id="login-username", placeholder="Username", type="text", className="mb-3"),
# # # # # #                 dbc.Input(id="login-password", placeholder="Password", type="password", className="mb-3"),
# # # # # #                 dbc.Button("Login", id="login-button", color="success", className="w-100"),
# # # # # #                 html.Div(id="login-alert-placeholder", className="mt-3")
# # # # # #             ])
# # # # # #         ], className="shadow"), width=10, sm=8, md=6, lg=4), justify="center",
# # # # # #             className="min-vh-100 align-items-center"),
# # # # # #
# # # # # #         dbc.Alert([
# # # # # #             html.H5("Demo Credentials", className="alert-heading"),
# # # # # #             html.P("Use the following details to log in:"),
# # # # # #             html.Hr(),
# # # # # #             html.P([html.B("Admin: "), "username: ", html.Code("admin"), ", password: ", html.Code("admin123")]),
# # # # # #             html.P([html.B("Cooperative Usernames: "), html.Code("kcu"), ", ", html.Code("mbeyacof"), ", ",
# # # # # #                     html.Code("dodoma_coop")]),
# # # # # #             html.P([html.B("Cooperative Password: "), "all use ", html.Code("coop123")]),
# # # # # #         ], color="info",
# # # # # #             style={"position": "absolute", "bottom": "10px", "left": "10px", "width": "auto", "maxWidth": "550px"})
# # # # # #     ], fluid=True, className="bg-light")
# # # # # #
# # # # # #
# # # # # # def create_cooperative_layout(session_data):
# # # # # #     return html.Div([
# # # # # #         dbc.NavbarSimple(brand=session_data.get('cooperative_name'),
# # # # # #                          children=[dbc.Button("Logout", id="logout-button", color="light", outline=True)],
# # # # # #                          color="success", dark=True),
# # # # # #         dbc.Container([
# # # # # #             dbc.Alert(id="coop-alert", is_open=False, duration=4000),
# # # # # #             html.H3("Co-operatives Farmer Data Submission  Portal", className="my-4"),
# # # # # #             dcc.Upload(
# # # # # #                 id='upload-data',
# # # # # #                 children=html.Div(['Drag and Drop or ', html.A('Select a CSV/Excel File')]),
# # # # # #                 style={'width': '100%', 'height': '60px', 'lineHeight': '60px', 'borderWidth': '1px',
# # # # # #                        'borderStyle': 'dashed', 'borderRadius': '5px', 'textAlign': 'center', 'margin': '10px 0'},
# # # # # #                 multiple=False
# # # # # #             ),
# # # # # #             html.Hr(),
# # # # # #             html.Div(id="submission-table-placeholder"),
# # # # # #             html.Hr(),
# # # # # #             html.H3("Submission History", className="my-4"),
# # # # # #             html.Div(id="coop-history-placeholder"),
# # # # # #         ], fluid=True),
# # # # # #         dbc.Modal(id="coop-results-modal", size="xl", is_open=False)
# # # # # #     ])
# # # # # #
# # # # # #
# # # # # # def create_admin_layout(session_data):
# # # # # #     return html.Div([
# # # # # #         dbc.Toast(
# # # # # #             id="ipn-toast",
# # # # # #             is_open=False,
# # # # # #             duration=6000,
# # # # # #             icon="success",
# # # # # #             style={"position": "fixed", "top": 20, "right": 20, "width": 350, "zIndex": 9999}
# # # # # #         ),
# # # # # #         dbc.NavbarSimple(brand="Union Admin Payments Dashboard",
# # # # # #                          children=[dbc.Button("Logout", id="logout-button", color="light", outline=True)],
# # # # # #                          color="primary", dark=True),
# # # # # #         dbc.Container([
# # # # # #             html.Div(id="admin-dashboard-content"),
# # # # # #             html.Hr(),
# # # # # #             html.H3("Payment History", className="my-4"),
# # # # # #             dbc.Button("Show/Hide History", id="toggle-history-btn", className="mb-3"),
# # # # # #             dbc.Collapse(
# # # # # #                 html.Div(id="payment-history-placeholder"),
# # # # # #                 id="history-collapse",
# # # # # #                 is_open=False
# # # # # #             )
# # # # # #         ], fluid=True, className="py-4"),
# # # # # #         dbc.Modal(id="details-modal", size="xl", is_open=False),
# # # # # #         dbc.Modal([
# # # # # #             dbc.ModalHeader("Processing Payment"),
# # # # # #             dbc.ModalBody(id="payment-animation-placeholder"),
# # # # # #             dbc.ModalFooter(dbc.Button("Close", id="payment-close-button", color="secondary", disabled=True))
# # # # # #         ], id="payment-modal", backdrop="static")
# # # # # #     ])
# # # # # #
# # # # # #
# # # # # # # Main App Layout
# # # # # # app.layout = html.Div([
# # # # # #     dcc.Store(id="user-session", storage_type="session"),
# # # # # #     dcc.Store(id="batch-to-process"),
# # # # # #     dcc.Store(id='ipn-data-store'),
# # # # # #     dcc.Interval(id='payment-interval', interval=2000, n_intervals=0, disabled=True),
# # # # # #     html.Div(id="main-content")
# # # # # # ])
# # # # # #
# # # # # #
# # # # # # # --- Callbacks ---
# # # # # #
# # # # # # # 1. Main Router
# # # # # # @app.callback(Output("main-content", "children"), Input("user-session", "data"))
# # # # # # def display_page(session_data):
# # # # # #     if session_data:
# # # # # #         if session_data.get("role") == "admin":
# # # # # #             return create_admin_layout(session_data)
# # # # # #         elif session_data.get("role") == "cooperative":
# # # # # #             return create_cooperative_layout(session_data)
# # # # # #     return create_login_layout()
# # # # # #
# # # # # #
# # # # # # # 2. Login
# # # # # # @app.callback(
# # # # # #     Output("user-session", "data"),
# # # # # #     Output("login-alert-placeholder", "children"),
# # # # # #     Input("login-button", "n_clicks"),
# # # # # #     State("login-username", "value"),
# # # # # #     State("login-password", "value"),
# # # # # #     prevent_initial_call=True
# # # # # # )
# # # # # # def handle_login(n_clicks, username, password):
# # # # # #     if not n_clicks:
# # # # # #         return dash.no_update, dash.no_update
# # # # # #
# # # # # #     if not username or not password:
# # # # # #         return dash.no_update, dbc.Alert("Fields cannot be empty.", color="warning")
# # # # # #
# # # # # #     user = authenticate_user(username, password)
# # # # # #     if user:
# # # # # #         return user, None
# # # # # #
# # # # # #     return None, dbc.Alert("Invalid credentials.", color="danger")
# # # # # #
# # # # # #
# # # # # # # 3. Logout
# # # # # # @app.callback(
# # # # # #     Output("user-session", "data", allow_duplicate=True),
# # # # # #     Input("logout-button", "n_clicks"),
# # # # # #     prevent_initial_call=True,
# # # # # # )
# # # # # # def handle_logout(n_clicks):
# # # # # #     if n_clicks:
# # # # # #         return None
# # # # # #     return dash.no_update
# # # # # #
# # # # # #
# # # # # # # 4. Cooperative: File Upload and Display
# # # # # # @app.callback(
# # # # # #     Output("submission-table-placeholder", "children"),
# # # # # #     Input('upload-data', 'contents'),
# # # # # #     State('upload-data', 'filename'),
# # # # # #     prevent_initial_call=True,
# # # # # # )
# # # # # # def update_output(contents, filename):
# # # # # #     if contents is None: return html.Div()
# # # # # #
# # # # # #     content_type, content_string = contents.split(',')
# # # # # #     decoded = base64.b64decode(content_string)
# # # # # #     try:
# # # # # #         df = pd.read_csv(io.StringIO(decoded.decode('utf-8'))) if 'csv' in filename else pd.read_excel(
# # # # # #             io.BytesIO(decoded))
# # # # # #         required_cols = {'farmer_name', 'bank_name', 'account_number', 'amount'}
# # # # # #         if not required_cols.issubset(df.columns):
# # # # # #             return dbc.Alert(f"File is missing columns: {required_cols - set(df.columns)}", color="danger")
# # # # # #
# # # # # #         return html.Div([
# # # # # #             dcc.Store(id='submission-data', data={'df': df.to_dict('records'), 'filename': filename}),
# # # # # #             html.H5("Review and Edit Data"),
# # # # # #             dash_table.DataTable(id='editable-datatable', data=df.to_dict('records'),
# # # # # #                                  columns=[{'name': i, 'id': i} for i in df.columns], page_size=10,
# # # # # #                                  style_table={'overflowX': 'auto'}, editable=True),
# # # # # #             html.Div([
# # # # # #                 dbc.Button("Submit to Admin", id="submit-to-admin-button", color="primary", className="mt-3"),
# # # # # #             ], className="d-flex justify-content-end gap-2")
# # # # # #         ])
# # # # # #     except Exception as e:
# # # # # #         return dbc.Alert(f"There was an error processing the file: {e}", color="danger")
# # # # # #
# # # # # #
# # # # # # # 5. Cooperative: Submit
# # # # # # @app.callback(
# # # # # #     Output("coop-alert", "children"), Output("coop-alert", "is_open"), Output("coop-alert", "color"),
# # # # # #     Output("submission-table-placeholder", "children", allow_duplicate=True),
# # # # # #     Input("submit-to-admin-button", "n_clicks"),
# # # # # #     State("editable-datatable", "data"), State("submission-data", "data"), State("user-session", "data"),
# # # # # #     prevent_initial_call=True,
# # # # # # )
# # # # # # def submit_to_admin(n_clicks, table_data, submission_data_store, session_data):
# # # # # #     if not n_clicks or not table_data:
# # # # # #         return "", False, "", dash.no_update
# # # # # #
# # # # # #     df = pd.DataFrame(table_data)
# # # # # #     filename = submission_data_store.get('filename', 'uploaded_file')
# # # # # #
# # # # # #     conn = sqlite3.connect('capital_pay_simplified.db')
# # # # # #     cursor = conn.cursor()
# # # # # #     try:
# # # # # #         cursor.execute(
# # # # # #             "INSERT INTO submission_batches (cooperative_id, filename, record_count, total_amount, submission_timestamp, status) VALUES (?, ?, ?, ?, ?, ?)",
# # # # # #             (session_data['id'], filename, len(df), df['amount'].sum(), datetime.now(),
# # # # # #              'pending_approval'))
# # # # # #         batch_id = cursor.lastrowid
# # # # # #         df_to_db = df[['farmer_name', 'bank_name', 'account_number', 'amount']]
# # # # # #         df_to_db['batch_id'] = batch_id
# # # # # #         df_to_db.to_sql('farmer_payments', conn, if_exists='append', index=False)
# # # # # #         conn.commit()
# # # # # #         msg, color = f"Successfully submitted {len(df)} records from {filename}.", "success"
# # # # # #         return msg, True, color, html.Div()
# # # # # #     except Exception as e:
# # # # # #         conn.rollback()
# # # # # #         msg, color = f"Database error: {e}", "danger"
# # # # # #     finally:
# # # # # #         conn.close()
# # # # # #     return msg, True, color, dash.no_update
# # # # # #
# # # # # #
# # # # # # # 6. Admin: Render Dashboard
# # # # # # @app.callback(
# # # # # #     Output("admin-dashboard-content", "children"),
# # # # # #     Input("user-session", "data"),
# # # # # #     Input("payment-close-button", "n_clicks"),
# # # # # #     Input("ipn-data-store", "data")
# # # # # # )
# # # # # # def render_admin_dashboard(session_data, close_clicks, ipn_data):
# # # # # #     if not session_data or session_data.get("role") != "admin": return None
# # # # # #
# # # # # #     triggered_id = callback_context.triggered_id
# # # # # #     if triggered_id is None and not session_data:
# # # # # #         return None
# # # # # #
# # # # # #     conn = sqlite3.connect('capital_pay_simplified.db')
# # # # # #     query = "SELECT b.id, u.cooperative_name, b.filename, b.record_count, b.total_amount, b.submission_timestamp FROM submission_batches b JOIN users u ON b.cooperative_id = u.id WHERE b.status = 'pending_approval' ORDER BY b.submission_timestamp DESC"
# # # # # #     batches_df = pd.read_sql_query(query, conn)
# # # # # #     conn.close()
# # # # # #
# # # # # #     if batches_df.empty: return dbc.Alert("No Pending Payments found.", color="info", className="m-4")
# # # # # #     cards = [
# # # # # #         dbc.Card([
# # # # # #             dbc.CardHeader(f"From: {row['cooperative_name']}"),
# # # # # #             dbc.CardBody([
# # # # # #                 html.H5(row['filename'], className="card-title"),
# # # # # #                 html.P(f"{row['record_count']} farmers, Total Amount: TSH {row['total_amount']:,.2f}"),
# # # # # #                 html.Small(
# # # # # #                     f"Submitted: {datetime.strptime(row['submission_timestamp'].split('.')[0], '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d %I:%M %p')}",
# # # # # #                     className="text-muted"),
# # # # # #             ]),
# # # # # #             dbc.CardFooter(html.Div([
# # # # # #                 dbc.Button("View Details", id={'type': 'view-details-btn', 'index': row['id']}, color="secondary"),
# # # # # #                 dbc.Button("Pay Now", id={'type': 'pay-now-btn', 'index': row['id']}, color="success"),
# # # # # #             ], className="d-flex justify-content-between"))
# # # # # #         ], className="mb-3") for _, row in batches_df.iterrows()
# # # # # #     ]
# # # # # #     return [html.H3("Pending Payments", className="mb-4")] + cards
# # # # # #
# # # # # #
# # # # # # # 7. Admin: View Details Modal and Save Notes
# # # # # # @app.callback(
# # # # # #     Output("details-modal", "is_open"), Output("details-modal", "children"),
# # # # # #     Input({'type': 'view-details-btn', 'index': ALL}, 'n_clicks'),
# # # # # #     prevent_initial_call=True
# # # # # # )
# # # # # # def toggle_details_modal(n_clicks):
# # # # # #     if not any(n_clicks): return False, None
# # # # # #     batch_id = int(eval(callback_context.triggered[0]['prop_id'].split('.')[0])['index'])
# # # # # #     conn = sqlite3.connect('capital_pay_simplified.db')
# # # # # #     df = pd.read_sql_query(
# # # # # #         "SELECT farmer_name, bank_name, account_number, amount FROM farmer_payments WHERE batch_id = ?", conn,
# # # # # #         params=(batch_id,))
# # # # # #     note_df = pd.read_sql_query("SELECT admin_notes FROM submission_batches WHERE id = ?", conn, params=(batch_id,))
# # # # # #     conn.close()
# # # # # #
# # # # # #     current_note = note_df['admin_notes'].iloc[0] or ""
# # # # # #
# # # # # #     return True, [
# # # # # #         dbc.ModalHeader(f"Submission Details (Batch ID: {batch_id})"),
# # # # # #         dbc.ModalBody([
# # # # # #             dash_table.DataTable(data=df.to_dict('records'), columns=[{'name': i, 'id': i} for i in df.columns],
# # # # # #                                  style_table={'overflowX': 'auto', 'maxHeight': '40vh', 'overflowY': 'auto'},
# # # # # #                                  editable=True, style_data_conditional=[
# # # # # #                     {'if': {'filter_query': '{amount} > 400000'}, 'backgroundColor': '#d4edda', 'color': '#155724'},
# # # # # #                     {'if': {'filter_query': '{amount} < 100000'}, 'backgroundColor': '#fff3cd', 'color': '#856404'}]),
# # # # # #             html.Hr(),
# # # # # #             html.H5("Admin Notes for Cooperative"),
# # # # # #             dbc.Alert(id="note-save-alert", is_open=False, duration=3000),
# # # # # #             dcc.Textarea(id={'type': 'admin-note-textarea', 'index': batch_id}, value=current_note,
# # # # # #                          style={'width': '100%', 'height': 100}),
# # # # # #             dbc.Button("Save Note", id={'type': 'save-note-btn', 'index': batch_id}, color="primary", className="mt-2")
# # # # # #         ])
# # # # # #     ]
# # # # # #
# # # # # #
# # # # # # @app.callback(
# # # # # #     Output("note-save-alert", "is_open"), Output("note-save-alert", "children"), Output("note-save-alert", "color"),
# # # # # #     Input({'type': 'save-note-btn', 'index': ALL}, 'n_clicks'),
# # # # # #     State({'type': 'admin-note-textarea', 'index': ALL}, 'value'),
# # # # # #     prevent_initial_call=True
# # # # # # )
# # # # # # def save_admin_note(n_clicks, notes):
# # # # # #     if not any(n_clicks): return False, "", ""
# # # # # #
# # # # # #     ctx = callback_context.triggered[0]
# # # # # #     batch_id = int(eval(ctx['prop_id'].split('.')[0])['index'])
# # # # # #     note_value = notes[0]
# # # # # #
# # # # # #     try:
# # # # # #         conn = sqlite3.connect('capital_pay_simplified.db')
# # # # # #         cursor = conn.cursor()
# # # # # #         cursor.execute("UPDATE submission_batches SET admin_notes = ? WHERE id = ?", (note_value, batch_id))
# # # # # #         conn.commit()
# # # # # #         conn.close()
# # # # # #         return True, "Note saved successfully!", "success"
# # # # # #     except Exception as e:
# # # # # #         return True, f"Error saving note: {e}", "danger"
# # # # # #
# # # # # #
# # # # # # # 8. Admin: Payment Processing
# # # # # # PAYMENT_STEPS = ["Initiating Capital Pay secure engine...", "Pre-processing and validating farmer data...",
# # # # # #                  "Connecting to inter-bank payment gateway...", "Securely settling respective farmers' accounts...",
# # # # # #                  "Transactions successful! Finalizing report..."]
# # # # # #
# # # # # #
# # # # # # @app.callback(
# # # # # #     Output("payment-modal", "is_open"), Output("payment-interval", "disabled"),
# # # # # #     Output("payment-animation-placeholder", "children"), Output("payment-close-button", "disabled"),
# # # # # #     Output("batch-to-process", "data"), Output("ipn-data-store", "data"),
# # # # # #     Output("admin-dashboard-content", "children", allow_duplicate=True),
# # # # # #     Output("payment-history-placeholder", "children", allow_duplicate=True),
# # # # # #     Input({'type': 'pay-now-btn', 'index': ALL}, 'n_clicks'),
# # # # # #     Input("payment-interval", "n_intervals"), Input("payment-close-button", "n_clicks"),
# # # # # #     State("batch-to-process", "data"),
# # # # # #     State("user-session", "data"),
# # # # # #     State("history-collapse", "is_open"),
# # # # # #     prevent_initial_call=True
# # # # # # )
# # # # # # def handle_payment_processing(pay_clicks, n_intervals, close_clicks, batch_id, session_data, history_is_open):
# # # # # #     if not callback_context.triggered: return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update
# # # # # #
# # # # # #     triggered_id = callback_context.triggered_id
# # # # # #     if triggered_id and isinstance(triggered_id, dict) and triggered_id.get("type") == "pay-now-btn" and any(
# # # # # #             pay_clicks):
# # # # # #         new_batch_id = int(triggered_id['index'])
# # # # # #         animation_step = html.Div([html.Div("🔄", style={'fontSize': 50, 'textAlign': 'center'}),
# # # # # #                                    dbc.Progress(value=5, className="mb-2", striped=True, animated=True),
# # # # # #                                    html.P(PAYMENT_STEPS[0], className="text-center")])
# # # # # #         return True, False, animation_step, True, new_batch_id, dash.no_update, dash.no_update, dash.no_update
# # # # # #
# # # # # #     if triggered_id == 'payment-interval' and batch_id is not None:
# # # # # #         step_index = n_intervals
# # # # # #         if step_index < len(PAYMENT_STEPS):
# # # # # #             progress = int(((step_index + 1) / len(PAYMENT_STEPS)) * 100)
# # # # # #             animation_step = html.Div([html.Div("🔄", style={'fontSize': 50, 'textAlign': 'center'}),
# # # # # #                                        dbc.Progress(value=progress, className="mb-2", striped=True, animated=True,
# # # # # #                                                     style={"height": "20px"}),
# # # # # #                                        html.P(PAYMENT_STEPS[step_index], className="text-center")])
# # # # # #             return True, False, animation_step, True, batch_id, dash.no_update, dash.no_update, dash.no_update
# # # # # #         else:
# # # # # #             conn = sqlite3.connect('capital_pay_simplified.db')
# # # # # #             cursor = conn.cursor()
# # # # # #
# # # # # #             cursor.execute(
# # # # # #                 "SELECT cooperative_id, u.cooperative_name, b.filename, b.record_count, b.total_amount FROM submission_batches b JOIN users u ON b.cooperative_id = u.id WHERE b.id = ?",
# # # # # #                 (batch_id,))
# # # # # #             batch_info = cursor.fetchone()
# # # # # #
# # # # # #             cursor.execute("UPDATE submission_batches SET status = 'processed' WHERE id = ?", (batch_id,))
# # # # # #
# # # # # #             payments_to_update, success_count, failed_count = [], 0, 0
# # # # # #             failure_reasons = ["Invalid Account Number", "Bank Network Error", "Account Closed", "Name Mismatch"]
# # # # # #             cursor.execute("SELECT id FROM farmer_payments WHERE batch_id = ?", (batch_id,))
# # # # # #             for (pid,) in cursor.fetchall():
# # # # # #                 if random.random() < 0.9:
# # # # # #                     payments_to_update.append(('paid', None, pid));
# # # # # #                     success_count += 1
# # # # # #                 else:
# # # # # #                     payments_to_update.append(('failed', random.choice(failure_reasons), pid));
# # # # # #                     failed_count += 1
# # # # # #             cursor.executemany("UPDATE farmer_payments SET status = ?, failure_reason = ? WHERE id = ?",
# # # # # #                                payments_to_update)
# # # # # #
# # # # # #             if batch_info:
# # # # # #                 coop_id, coop_name, filename, record_count, total_amount = batch_info
# # # # # #                 cursor.execute(
# # # # # #                     "INSERT INTO payment_history (batch_id, cooperative_id, cooperative_name, filename, record_count, total_amount, processing_timestamp) VALUES (?, ?, ?, ?, ?, ?, ?)",
# # # # # #                     (batch_id, coop_id, coop_name, filename, record_count, total_amount, datetime.now()))
# # # # # #
# # # # # #             conn.commit()
# # # # # #             conn.close()
# # # # # #
# # # # # #             ipn_data = {'coop_name': batch_info[1], 'success': success_count, 'failed': failed_count,
# # # # # #                         'total': batch_info[3]}
# # # # # #             result = html.Div([html.Div("✅", style={'fontSize': 60, 'textAlign': 'center', 'color': 'green'}),
# # # # # #                                dbc.Progress(value=100, color="success", className="mb-2"),
# # # # # #                                html.H5("Payment Processed!", className="text-success text-center")])
# # # # # #
# # # # # #             updated_admin_dashboard = render_admin_dashboard(session_data, None, ipn_data)
# # # # # #             updated_payment_history_content = render_payment_history(history_is_open, ipn_data)
# # # # # #
# # # # # #             return True, True, result, False, None, ipn_data, updated_admin_dashboard, updated_payment_history_content
# # # # # #
# # # # # #     if triggered_id == 'payment-close-button':
# # # # # #         updated_admin_dashboard = render_admin_dashboard(session_data, close_clicks, None)
# # # # # #         return False, True, "", True, None, None, updated_admin_dashboard, dash.no_update
# # # # # #
# # # # # #     return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update
# # # # # #
# # # # # #
# # # # # # # 9. IPN Toast Notification
# # # # # # @app.callback(
# # # # # #     Output("ipn-toast", "is_open"), Output("ipn-toast", "header"),
# # # # # #     Output("ipn-toast", "children"), Output("ipn-toast", "icon"),
# # # # # #     Input("ipn-data-store", "data"),
# # # # # #     prevent_initial_call=True
# # # # # # )
# # # # # # def show_ipn_toast(data):
# # # # # #     if not data: return False, "", "", ""
# # # # # #     header = "IPN: Transaction Complete"
# # # # # #     icon = "success" if data['failed'] == 0 else "warning"
# # # # # #     body = f"{data['coop_name']}: Paid {data['success']}/{data['total']} farmers. ({data['failed']} failed)"
# # # # # #     return True, header, body, icon
# # # # # #
# # # # # #
# # # # # # # 10. Cooperative History and Results
# # # # # # @app.callback(
# # # # # #     Output("coop-history-placeholder", "children"),
# # # # # #     Input("user-session", "data"),
# # # # # #     Input("coop-alert", "is_open"),
# # # # # #     Input("ipn-data-store", "data"),
# # # # # #     State("user-session", "data"),
# # # # # #     prevent_initial_call=False
# # # # # # )
# # # # # # def render_coop_history(session_trigger, alert_is_open, ipn_data, session_data):
# # # # # #     if not session_data or session_data.get("role") != "cooperative": return None
# # # # # #
# # # # # #     conn = sqlite3.connect('capital_pay_simplified.db')
# # # # # #     df = pd.read_sql_query(
# # # # # #         "SELECT id, filename, status, submission_timestamp, admin_notes FROM submission_batches WHERE cooperative_id = ? ORDER BY submission_timestamp DESC",
# # # # # #         conn, params=(session_data['id'],))
# # # # # #     conn.close()
# # # # # #     if df.empty: return dbc.Alert("No submissions yet.", color="info")
# # # # # #
# # # # # #     return dbc.Accordion([
# # # # # #         dbc.AccordionItem([
# # # # # #             html.P(
# # # # # #                 f"Submitted on: {datetime.strptime(row['submission_timestamp'].split('.')[0], '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d %I:%M %p')}"),
# # # # # #             dbc.Alert(f"Admin Note: {row['admin_notes']}", color="info") if row['admin_notes'] else "",
# # # # # #             dbc.Button("View Results", id={'type': 'view-results-btn', 'index': row['id']}, color="info", size="sm") if
# # # # # #             row['status'] == 'processed' else ""
# # # # # #         ], title=html.Div([row['filename'], dbc.Badge(row['status'].replace('_', ' ').title(),
# # # # # #                                                       color="success" if row['status'] == 'processed' else "warning",
# # # # # #                                                       className="ms-2")]))
# # # # # #         for _, row in df.iterrows()
# # # # # #     ], start_collapsed=True)
# # # # # #
# # # # # #
# # # # # # @app.callback(
# # # # # #     Output('coop-results-modal', 'is_open'), Output('coop-results-modal', 'children'),
# # # # # #     Input({'type': 'view-results-btn', 'index': ALL}, 'n_clicks'),
# # # # # #     prevent_initial_call=True
# # # # # # )
# # # # # # def show_coop_results_modal(n_clicks):
# # # # # #     if not any(n_clicks): return False, None
# # # # # #     batch_id = int(eval(callback_context.triggered[0]['prop_id'].split('.')[0])['index'])
# # # # # #     conn = sqlite3.connect('capital_pay_simplified.db')
# # # # # #     df = pd.read_sql_query(
# # # # # #         "SELECT farmer_name, bank_name, account_number, amount, status, failure_reason FROM farmer_payments WHERE batch_id = ?",
# # # # # #         conn, params=(batch_id,))
# # # # # #     conn.close()
# # # # # #     return True, [
# # # # # #         dbc.ModalHeader(f"Payment Results (Batch ID: {batch_id})"),
# # # # # #         dbc.ModalBody(dash_table.DataTable(
# # # # # #             data=df.to_dict('records'),
# # # # # #             columns=[{'name': i.replace('_', ' ').title(), 'id': i} for i in df.columns],
# # # # # #             style_table={'overflowX': 'auto'}, editable=False,
# # # # # #             style_data_conditional=[
# # # # # #                 {'if': {'filter_query': '{status} = "paid"'}, 'backgroundColor': '#d4edda', 'color': '#155724'},
# # # # # #                 {'if': {'filter_query': '{status} = "failed"'}, 'backgroundColor': '#f8d7da', 'color': '#721c24'}
# # # # # #             ]
# # # # # #         ))
# # # # # #     ]
# # # # # #
# # # # # #
# # # # # # # 11. Admin: Payment History
# # # # # # @app.callback(
# # # # # #     Output("history-collapse", "is_open"),
# # # # # #     Input("toggle-history-btn", "n_clicks"),
# # # # # #     State("history-collapse", "is_open"),
# # # # # #     prevent_initial_call=True
# # # # # # )
# # # # # # def toggle_history_collapse(n, is_open):
# # # # # #     if n: return not is_open
# # # # # #     return is_open
# # # # # #
# # # # # #
# # # # # # @app.callback(
# # # # # #     Output("payment-history-placeholder", "children"),
# # # # # #     Input("history-collapse", "is_open"),
# # # # # #     Input("ipn-data-store", "data"),
# # # # # #     prevent_initial_call=False
# # # # # # )
# # # # # # def render_payment_history(is_open, ipn_data):
# # # # # #     if not is_open: return dash.no_update
# # # # # #     conn = sqlite3.connect('capital_pay_simplified.db')
# # # # # #     history_df = pd.read_sql_query(
# # # # # #         "SELECT ph.id, u.cooperative_name, ph.filename, ph.record_count, ph.total_amount, ph.processing_timestamp FROM payment_history ph JOIN users u ON ph.cooperative_id = u.id ORDER BY ph.processing_timestamp DESC", conn)
# # # # # #     conn.close()
# # # # # #     if history_df.empty: return dbc.Alert("No processed payments found.", color="secondary")
# # # # # #     return dash_table.DataTable(data=history_df.to_dict('records'),
# # # # # #                                 columns=[{'name': i.replace('_', ' ').title(), 'id': i} for i in history_df.columns],
# # # # # #                                 page_size=20, style_table={'overflowX': 'auto'}, editable=False)
# # # # # #
# # # # # #
# # # # # # # --- Run Application ---
# # # # # # if __name__ == "__main__":
# # # # # #     init_db()
# # # # # #     app.run(debug=True, port=8055)
# # # # #
# # # # #
# # # # # import dash
# # # # # from dash import dcc, html, Input, Output, State, dash_table, callback_context, ALL
# # # # # import dash_bootstrap_components as dbc
# # # # # import pandas as pd
# # # # # import sqlite3
# # # # # import hashlib
# # # # # from datetime import datetime
# # # # # import base64
# # # # # import io
# # # # # import random
# # # # #
# # # # # # Initialize Dash app
# # # # # app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP], suppress_callback_exceptions=True)
# # # # # app.title = "Capital Pay - Simplified Payment System"
# # # # #
# # # # #
# # # # # # --- Database Setup ---
# # # # # def init_db():
# # # # #     conn = sqlite3.connect('capital_pay_simplified.db')
# # # # #     cursor = conn.cursor()
# # # # #
# # # # #     # Users table
# # # # #     cursor.execute('''
# # # # #         CREATE TABLE IF NOT EXISTS users (
# # # # #             id INTEGER PRIMARY KEY AUTOINCREMENT,
# # # # #             username TEXT UNIQUE NOT NULL,
# # # # #             password TEXT NOT NULL,
# # # # #             role TEXT NOT NULL,
# # # # #             cooperative_name TEXT
# # # # #         )
# # # # #     ''')
# # # # #
# # # # #     # Submission Batches table
# # # # #     cursor.execute('''
# # # # #         CREATE TABLE IF NOT EXISTS submission_batches (
# # # # #             id INTEGER PRIMARY KEY AUTOINCREMENT,
# # # # #             cooperative_id INTEGER,
# # # # #             filename TEXT,
# # # # #             record_count INTEGER,
# # # # #             total_amount REAL,
# # # # #             submission_timestamp TIMESTAMP,
# # # # #             status TEXT,
# # # # #             admin_notes TEXT,
# # # # #             cooperative_notes TEXT,
# # # # #             FOREIGN KEY (cooperative_id) REFERENCES users (id)
# # # # #         )
# # # # #     ''')
# # # # #
# # # # #     # Farmer Payments table
# # # # #     cursor.execute('''
# # # # #         CREATE TABLE IF NOT EXISTS farmer_payments (
# # # # #             id INTEGER PRIMARY KEY AUTOINCREMENT,
# # # # #             batch_id INTEGER,
# # # # #             farmer_name TEXT NOT NULL,
# # # # #             bank_name TEXT NOT NULL,
# # # # #             account_number TEXT NOT NULL,
# # # # #             amount REAL NOT NULL,
# # # # #             status TEXT DEFAULT 'pending',
# # # # #             failure_reason TEXT,
# # # # #             FOREIGN KEY (batch_id) REFERENCES submission_batches (id)
# # # # #         )
# # # # #     ''')
# # # # #
# # # # #     # Payment History table
# # # # #     cursor.execute('''
# # # # #         CREATE TABLE IF NOT EXISTS payment_history (
# # # # #             id INTEGER PRIMARY KEY AUTOINCREMENT,
# # # # #             batch_id INTEGER,
# # # # #             cooperative_name TEXT,
# # # # #             filename TEXT,
# # # # #             record_count INTEGER,
# # # # #             total_amount REAL,
# # # # #             processing_timestamp TIMESTAMP
# # # # #         )
# # # # #     ''')
# # # # #
# # # # #     # Activity Logs table
# # # # #     cursor.execute('''
# # # # #         CREATE TABLE IF NOT EXISTS activity_logs (
# # # # #             id INTEGER PRIMARY KEY AUTOINCREMENT,
# # # # #             timestamp TIMESTAMP,
# # # # #             user_id INTEGER,
# # # # #             cooperative_name TEXT,
# # # # #             action TEXT,
# # # # #             details TEXT,
# # # # #             FOREIGN KEY (user_id) REFERENCES users (id)
# # # # #         )
# # # # #     ''')
# # # # #
# # # # #     # Pre-populate with default users if table is empty
# # # # #     cursor.execute("SELECT COUNT(*) from users")
# # # # #     if cursor.fetchone()[0] == 0:
# # # # #         admin_password = hashlib.sha256("admin123".encode()).hexdigest()
# # # # #         coop_password = hashlib.sha256("coop123".encode()).hexdigest()
# # # # #         users_to_add = [
# # # # #             ("admin", admin_password, "admin", "Capital Pay Admin"),
# # # # #             ("kcu", coop_password, "cooperative", "Kilimanjaro Cooperative Union"),
# # # # #             ("mbeyacof", coop_password, "cooperative", "Mbeya Coffee Union"),
# # # # #         ]
# # # # #         for user in users_to_add:
# # # # #             cursor.execute(
# # # # #                 "INSERT OR IGNORE INTO users (username, password, role, cooperative_name) VALUES (?, ?, ?, ?)", user)
# # # # #
# # # # #     conn.commit()
# # # # #     conn.close()
# # # # #
# # # # #
# # # # # # --- Utility Functions ---
# # # # # def log_activity(user_id, action, details=""):
# # # # #     conn = sqlite3.connect('capital_pay_simplified.db')
# # # # #     cursor = conn.cursor()
# # # # #     cursor.execute("SELECT cooperative_name FROM users WHERE id = ?", (user_id,))
# # # # #     cooperative_name = cursor.fetchone()[0]
# # # # #     cursor.execute(
# # # # #         "INSERT INTO activity_logs (timestamp, user_id, cooperative_name, action, details) VALUES (?, ?, ?, ?, ?)",
# # # # #         (datetime.now(), user_id, cooperative_name, action, details))
# # # # #     conn.commit()
# # # # #     conn.close()
# # # # #
# # # # #
# # # # # def authenticate_user(username, password):
# # # # #     conn = sqlite3.connect('capital_pay_simplified.db')
# # # # #     cursor = conn.cursor()
# # # # #     cursor.execute("SELECT id, password, role, cooperative_name FROM users WHERE username = ?", (username,))
# # # # #     user = cursor.fetchone()
# # # # #     conn.close()
# # # # #     if user and user[1] == hashlib.sha256(password.encode()).hexdigest():
# # # # #         return {"id": user[0], "username": username, "role": user[2], "cooperative_name": user[3]}
# # # # #     return None
# # # # #
# # # # #
# # # # # # --- Layout Definitions ---
# # # # # def create_login_layout():
# # # # #     return dbc.Container([
# # # # #         dbc.Row(dbc.Col(dbc.Card([
# # # # #             dbc.CardBody([
# # # # #                 html.H2("Capital Pay", className="text-center mb-4 text-success"),
# # # # #                 dbc.Input(id="login-username", placeholder="Username", type="text", className="mb-3"),
# # # # #                 dbc.Input(id="login-password", placeholder="Password", type="password", className="mb-3"),
# # # # #                 dbc.Button("Login", id="login-button", color="success", className="w-100"),
# # # # #                 html.Div(id="login-alert-placeholder", className="mt-3")
# # # # #             ])
# # # # #         ], className="shadow"), width=10, sm=8, md=6, lg=4), justify="center",
# # # # #             className="min-vh-100 align-items-center"),
# # # # #         dbc.Alert([
# # # # #             html.H5("Demo Credentials", className="alert-heading"),
# # # # #             html.P([html.B("Admin: "), "username: ", html.Code("admin"), ", password: ", html.Code("admin123")]),
# # # # #             html.P([html.B("Cooperative: "), "username: ", html.Code("kcu"), ", password: ", html.Code("coop123")]),
# # # # #         ], color="info", style={"position": "absolute", "bottom": "10px", "left": "10px", "width": "auto"})
# # # # #     ], fluid=True, className="bg-light")
# # # # #
# # # # #
# # # # # def create_cooperative_layout(session_data):
# # # # #     return html.Div([
# # # # #         dbc.NavbarSimple(brand=session_data.get('cooperative_name'),
# # # # #                          children=[dbc.Button("Logout", id="logout-button", color="light", outline=True)],
# # # # #                          color="success", dark=True),
# # # # #         dbc.Container([
# # # # #             dbc.Alert(id="coop-alert", is_open=False, duration=4000),
# # # # #             html.H3("Farmer Data Submission  Portal", className="my-4"),
# # # # #             dcc.Upload(id='upload-data', children=html.Div(['Drag and Drop or ', html.A('Select a CSV/Excel File')]),
# # # # #                        style={'width': '100%', 'height': '60px', 'lineHeight': '60px', 'borderWidth': '1px',
# # # # #                               'borderStyle': 'dashed', 'borderRadius': '5px', 'textAlign': 'center',
# # # # #                               'margin': '10px 0'},
# # # # #                        multiple=False),
# # # # #             html.Hr(),
# # # # #             html.Div(id="submission-table-placeholder"),
# # # # #             html.Hr(),
# # # # #             html.H3("Submission History", className="my-4"),
# # # # #             html.Div(id="coop-history-placeholder"),
# # # # #         ], fluid=True),
# # # # #         dbc.Modal(id="coop-results-modal", size="xl", is_open=False)
# # # # #     ])
# # # # #
# # # # #
# # # # # def create_admin_layout(session_data):
# # # # #     return html.Div([
# # # # #         # NEW: Auto-refresh interval for the admin dashboard
# # # # #         dcc.Interval(id='admin-refresh-interval', interval=15 * 1000, n_intervals=0),  # 15 seconds
# # # # #         dbc.Toast(id="ipn-toast", is_open=False, duration=6000, icon="success",
# # # # #                   style={"position": "fixed", "top": 20, "right": 20, "width": 350, "zIndex": 9999}),
# # # # #         dbc.NavbarSimple(brand="Admin Payments Dashboard",
# # # # #                          children=[dbc.Button("Logout", id="logout-button", color="light", outline=True)],
# # # # #                          color="primary", dark=True),
# # # # #         dbc.Container([
# # # # #             html.Div(id="admin-dashboard-content"),
# # # # #             html.Hr(),
# # # # #             html.H3("Payment History", className="my-4"),
# # # # #             dbc.Button("Show/Hide History", id="toggle-history-btn", className="mb-3"),
# # # # #             dbc.Collapse(html.Div(id="payment-history-placeholder"), id="history-collapse", is_open=False),
# # # # #             html.Hr(),
# # # # #             html.H3("User Activity Logs", className="my-4"),
# # # # #             dbc.Button("Show/Hide Logs", id="toggle-logs-btn", className="mb-3"),
# # # # #             dbc.Collapse(html.Div(id="activity-logs-placeholder"), id="logs-collapse", is_open=False),
# # # # #         ], fluid=True, className="py-4"),
# # # # #         dbc.Modal(id="details-modal", size="xl", is_open=False),
# # # # #         dbc.Modal([
# # # # #             dbc.ModalHeader("Processing Payment"),
# # # # #             dbc.ModalBody(id="payment-animation-placeholder"),
# # # # #             dbc.ModalFooter(dbc.Button("Close", id="payment-close-button", color="secondary", disabled=True))
# # # # #         ], id="payment-modal", backdrop="static")
# # # # #     ])
# # # # #
# # # # #
# # # # # # Main App Layout
# # # # # app.layout = html.Div([
# # # # #     dcc.Store(id="user-session", storage_type="session"),
# # # # #     dcc.Store(id="batch-to-process"),
# # # # #     dcc.Store(id='ipn-data-store'),
# # # # #     dcc.Interval(id='payment-interval', interval=1500, n_intervals=0, disabled=True),
# # # # #     html.Div(id="main-content")
# # # # # ])
# # # # #
# # # # #
# # # # # # --- Callbacks ---
# # # # # @app.callback(Output("main-content", "children"), Input("user-session", "data"))
# # # # # def display_page(session_data):
# # # # #     if session_data:
# # # # #         if session_data.get("role") == "admin":
# # # # #             return create_admin_layout(session_data)
# # # # #         elif session_data.get("role") == "cooperative":
# # # # #             return create_cooperative_layout(session_data)
# # # # #     return create_login_layout()
# # # # #
# # # # #
# # # # # @app.callback(Output("user-session", "data"), Output("login-alert-placeholder", "children"),
# # # # #               Input("login-button", "n_clicks"), State("login-username", "value"), State("login-password", "value"),
# # # # #               prevent_initial_call=True)
# # # # # def handle_login(n_clicks, username, password):
# # # # #     if not username or not password: return dash.no_update, dbc.Alert("Fields cannot be empty.", color="warning")
# # # # #     user = authenticate_user(username, password)
# # # # #     if user:
# # # # #         log_activity(user['id'], 'Login', f"User '{user['username']}' logged in.")
# # # # #         return user, None
# # # # #     return None, dbc.Alert("Invalid credentials.", color="danger")
# # # # #
# # # # #
# # # # # @app.callback(Output("user-session", "data", allow_duplicate=True), Input("logout-button", "n_clicks"),
# # # # #               prevent_initial_call=True)
# # # # # def handle_logout(n_clicks):
# # # # #     if n_clicks: return None
# # # # #     return dash.no_update
# # # # #
# # # # #
# # # # # @app.callback(Output("submission-table-placeholder", "children"), Input('upload-data', 'contents'),
# # # # #               State('upload-data', 'filename'), prevent_initial_call=True)
# # # # # def update_output(contents, filename):
# # # # #     if contents is None: return html.Div()
# # # # #     content_type, content_string = contents.split(',')
# # # # #     decoded = base64.b64decode(content_string)
# # # # #     try:
# # # # #         df = pd.read_csv(io.StringIO(decoded.decode('utf-8'))) if 'csv' in filename else pd.read_excel(
# # # # #             io.BytesIO(decoded))
# # # # #         required_cols = {'farmer_name', 'bank_name', 'account_number', 'amount'}
# # # # #         if not required_cols.issubset(df.columns): return dbc.Alert(
# # # # #             f"File is missing columns: {required_cols - set(df.columns)}", color="danger")
# # # # #         return html.Div([
# # # # #             dcc.Store(id='submission-data', data={'df': df.to_dict('records'), 'filename': filename}),
# # # # #             html.H5("Review Data"),
# # # # #             dash_table.DataTable(id='editable-datatable', data=df.to_dict('records'),
# # # # #                                  columns=[{'name': i, 'id': i} for i in df.columns], page_size=10,
# # # # #                                  style_table={'overflowX': 'auto'}, editable=True),
# # # # #             html.Hr(),
# # # # #             dbc.Label("Note to Admin (Optional)", html_for="coop-note-textarea"),
# # # # #             dbc.Textarea(id='coop-note-textarea', placeholder="Add notes for the admin regarding this submission...",
# # # # #                          className="mb-3"),
# # # # #             html.Div(dbc.Button("Submit to Admin", id="submit-to-admin-button", color="primary"),
# # # # #                      className="d-flex justify-content-end")
# # # # #         ])
# # # # #     except Exception as e:
# # # # #         return dbc.Alert(f"Error processing file: {e}", color="danger")
# # # # #
# # # # #
# # # # # @app.callback(Output("coop-alert", "children"), Output("coop-alert", "is_open"), Output("coop-alert", "color"),
# # # # #               Output("submission-table-placeholder", "children", allow_duplicate=True),
# # # # #               Input("submit-to-admin-button", "n_clicks"), State("editable-datatable", "data"),
# # # # #               State("submission-data", "data"), State("user-session", "data"), State("coop-note-textarea", "value"),
# # # # #               prevent_initial_call=True)
# # # # # def submit_to_admin(n_clicks, table_data, submission_data_store, session_data, coop_note):
# # # # #     if not n_clicks or not table_data: return "", False, "", dash.no_update
# # # # #     df = pd.DataFrame(table_data)
# # # # #     filename = submission_data_store.get('filename', 'uploaded_file')
# # # # #     conn = sqlite3.connect('capital_pay_simplified.db')
# # # # #     cursor = conn.cursor()
# # # # #     try:
# # # # #         cursor.execute(
# # # # #             "INSERT INTO submission_batches (cooperative_id, filename, record_count, total_amount, submission_timestamp, status, cooperative_notes) VALUES (?, ?, ?, ?, ?, ?, ?)",
# # # # #             (session_data['id'], filename, len(df), df['amount'].sum(), datetime.now(), 'pending_approval', coop_note))
# # # # #         batch_id = cursor.lastrowid
# # # # #         df_to_db = df[['farmer_name', 'bank_name', 'account_number', 'amount']]
# # # # #         df_to_db['batch_id'] = batch_id
# # # # #         df_to_db.to_sql('farmer_payments', conn, if_exists='append', index=False)
# # # # #         conn.commit()
# # # # #         log_activity(session_data['id'], 'Data Submission', f"Submitted '{filename}' with {len(df)} records.")
# # # # #         msg, color = f"Successfully submitted {len(df)} records.", "success"
# # # # #         return msg, True, color, html.Div()
# # # # #     except Exception as e:
# # # # #         conn.rollback();
# # # # #         msg, color = f"Database error: {e}", "danger"
# # # # #     finally:
# # # # #         conn.close()
# # # # #     return msg, True, color, dash.no_update
# # # # #
# # # # #
# # # # # @app.callback(Output("admin-dashboard-content", "children"), Input("user-session", "data"),
# # # # #               Input("ipn-data-store", "data"), Input('admin-refresh-interval', 'n_intervals'))
# # # # # def render_admin_dashboard(session_data, ipn_data, n_intervals):
# # # # #     if not session_data or session_data.get("role") != "admin": return None
# # # # #     conn = sqlite3.connect('capital_pay_simplified.db')
# # # # #     query = "SELECT b.id, u.cooperative_name, b.filename, b.record_count, b.total_amount FROM submission_batches b JOIN users u ON b.cooperative_id = u.id WHERE b.status = 'pending_approval' ORDER BY b.submission_timestamp DESC"
# # # # #     batches_df = pd.read_sql_query(query, conn)
# # # # #     conn.close()
# # # # #     if batches_df.empty: return dbc.Alert("No Pending Payments found.", color="info", className="m-4")
# # # # #     cards = [dbc.Card([
# # # # #         dbc.CardHeader(f"From: {row['cooperative_name']}"),
# # # # #         dbc.CardBody([html.H5(row['filename'], className="card-title"),
# # # # #                       html.P(f"{row['record_count']} farmers, Total: TSH {row['total_amount']:,.2f}")]),
# # # # #         dbc.CardFooter(html.Div([
# # # # #             dbc.Button("View Details", id={'type': 'view-details-btn', 'index': row['id']}, color="secondary"),
# # # # #             dbc.Button("Pay Now", id={'type': 'pay-now-btn', 'index': row['id']}, color="success"),
# # # # #         ], className="d-flex justify-content-between"))
# # # # #     ], className="mb-3") for _, row in batches_df.iterrows()]
# # # # #     return [html.H3("Pending Payments", className="mb-4")] + cards
# # # # #
# # # # #
# # # # # @app.callback(Output("details-modal", "is_open"), Output("details-modal", "children"),
# # # # #               Input({'type': 'view-details-btn', 'index': ALL}, 'n_clicks'), prevent_initial_call=True)
# # # # # def toggle_details_modal(n_clicks):
# # # # #     if not any(n_clicks): return False, None
# # # # #     batch_id = int(eval(callback_context.triggered[0]['prop_id'].split('.')[0])['index'])
# # # # #     conn = sqlite3.connect('capital_pay_simplified.db')
# # # # #     df = pd.read_sql_query(
# # # # #         "SELECT farmer_name, bank_name, account_number, amount FROM farmer_payments WHERE batch_id = ?", conn,
# # # # #         params=(batch_id,))
# # # # #     notes_df = pd.read_sql_query("SELECT admin_notes, cooperative_notes FROM submission_batches WHERE id = ?", conn,
# # # # #                                  params=(batch_id,))
# # # # #     conn.close()
# # # # #     admin_note, coop_note = notes_df['admin_notes'].iloc[0] or "", notes_df['cooperative_notes'].iloc[0]
# # # # #     return True, [
# # # # #         dbc.ModalHeader(f"Submission Details (Batch ID: {batch_id})"),
# # # # #         dbc.ModalBody([
# # # # #             dash_table.DataTable(data=df.to_dict('records'), columns=[{'name': i, 'id': i} for i in df.columns],
# # # # #                                  style_table={'maxHeight': '40vh', 'overflowY': 'auto'}),
# # # # #             html.Hr(),
# # # # #             html.H5("Note from Cooperative"),
# # # # #             dbc.Alert(coop_note, color="info") if coop_note else html.P("No note provided.", className="text-muted"),
# # # # #             html.Hr(),
# # # # #             html.H5("Admin Notes for Cooperative"),
# # # # #             dbc.Alert(id="note-save-alert", is_open=False, duration=3000),
# # # # #             dcc.Textarea(id={'type': 'admin-note-textarea', 'index': batch_id}, value=admin_note,
# # # # #                          style={'width': '100%', 'height': 100}),
# # # # #             dbc.Button("Save Note", id={'type': 'save-note-btn', 'index': batch_id}, color="primary", className="mt-2")
# # # # #         ])
# # # # #     ]
# # # # #
# # # # #
# # # # # @app.callback(Output("note-save-alert", "is_open"), Output("note-save-alert", "children"),
# # # # #               Output("note-save-alert", "color"),
# # # # #               Input({'type': 'save-note-btn', 'index': ALL}, 'n_clicks'),
# # # # #               State({'type': 'admin-note-textarea', 'index': ALL}, 'value'),
# # # # #               prevent_initial_call=True)
# # # # # def save_admin_note(n_clicks, notes):
# # # # #     if not any(n_clicks): return False, "", ""
# # # # #     ctx = callback_context.triggered[0];
# # # # #     batch_id = int(eval(ctx['prop_id'].split('.')[0])['index']);
# # # # #     note_value = notes[0]
# # # # #     try:
# # # # #         conn = sqlite3.connect('capital_pay_simplified.db')
# # # # #         cursor = conn.cursor();
# # # # #         cursor.execute("UPDATE submission_batches SET admin_notes = ? WHERE id = ?", (note_value, batch_id));
# # # # #         conn.commit();
# # # # #         conn.close()
# # # # #         return True, "Note saved successfully!", "success"
# # # # #     except Exception as e:
# # # # #         return True, f"Error saving note: {e}", "danger"
# # # # #
# # # # #
# # # # # # FIX: handle_payment_processing now correctly saves to payment_history
# # # # # @app.callback(Output("payment-modal", "is_open"), Output("payment-interval", "disabled"),
# # # # #               Output("payment-animation-placeholder", "children"), Output("payment-close-button", "disabled"),
# # # # #               Output("batch-to-process", "data"), Output("ipn-data-store", "data"),
# # # # #               Input({'type': 'pay-now-btn', 'index': ALL}, 'n_clicks'), Input("payment-interval", "n_intervals"),
# # # # #               Input("payment-close-button", "n_clicks"),
# # # # #               State("batch-to-process", "data"), State("user-session", "data"), prevent_initial_call=True)
# # # # # def handle_payment_processing(pay_clicks, n_intervals, close_clicks, batch_id, session_data):
# # # # #     ctx_triggered = callback_context.triggered_id
# # # # #     if isinstance(ctx_triggered, dict) and ctx_triggered.get("type") == "pay-now-btn":
# # # # #         new_batch_id = int(ctx_triggered['index'])
# # # # #         animation_step = html.Div(
# # # # #             [html.Div("🔄", style={'fontSize': 50}), dbc.Progress(value=5), html.P("Initiating...")],
# # # # #             className="text-center")
# # # # #         return True, False, animation_step, True, new_batch_id, dash.no_update
# # # # #     if ctx_triggered == 'payment-interval' and batch_id is not None:
# # # # #         if n_intervals < 4:
# # # # #             progress = (n_intervals + 1) * 25
# # # # #             animation_step = html.Div(
# # # # #                 [html.Div("🔄", style={'fontSize': 50}), dbc.Progress(value=progress, striped=True, animated=True),
# # # # #                  html.P("Processing...")], className="text-center")
# # # # #             return True, False, animation_step, True, batch_id, dash.no_update
# # # # #         else:
# # # # #             conn = sqlite3.connect('capital_pay_simplified.db')
# # # # #             cursor = conn.cursor()
# # # # #             cursor.execute(
# # # # #                 "SELECT u.cooperative_name, b.filename, b.record_count, b.total_amount FROM submission_batches b JOIN users u ON b.cooperative_id = u.id WHERE b.id = ?",
# # # # #                 (batch_id,))
# # # # #             batch_info = cursor.fetchone()
# # # # #             cursor.execute("UPDATE submission_batches SET status = 'processed' WHERE id = ?", (batch_id,))
# # # # #             payments, success, failed = [], 0, 0
# # # # #             reasons = ["Invalid Account", "Bank Error", "Name Mismatch"]
# # # # #             cursor.execute("SELECT id FROM farmer_payments WHERE batch_id = ?", (batch_id,))
# # # # #             for (pid,) in cursor.fetchall():
# # # # #                 if random.random() < 0.95:
# # # # #                     success += 1; payments.append(('paid', None, pid))
# # # # #                 else:
# # # # #                     failed += 1; payments.append(('failed', random.choice(reasons), pid))
# # # # #             cursor.executemany("UPDATE farmer_payments SET status = ?, failure_reason = ? WHERE id = ?", payments)
# # # # #             # FIX: Insert record into payment_history table
# # # # #             if batch_info:
# # # # #                 coop_name, filename, record_count, total_amount = batch_info
# # # # #                 cursor.execute(
# # # # #                     "INSERT INTO payment_history (batch_id, cooperative_name, filename, record_count, total_amount, processing_timestamp) VALUES (?, ?, ?, ?, ?, ?)",
# # # # #                     (batch_id, coop_name, filename, record_count, total_amount, datetime.now()))
# # # # #             conn.commit()
# # # # #             conn.close()
# # # # #             log_activity(session_data['id'], 'Payment Processed',
# # # # #                          f"Processed '{batch_info[1]}' for {batch_info[0]}. Success: {success}, Failed: {failed}.")
# # # # #             ipn = {'coop': batch_info[0], 'success': success, 'failed': failed, 'total': batch_info[2]}
# # # # #             result = html.Div(
# # # # #                 [html.Div("✅", style={'fontSize': 60, 'color': 'green'}), dbc.Progress(value=100, color="success"),
# # # # #                  html.H5("Payment Processed!")], className="text-center")
# # # # #             return True, True, result, False, None, ipn
# # # # #     if ctx_triggered == 'payment-close-button': return False, True, "", True, None, dash.no_update
# # # # #     return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update
# # # # #
# # # # #
# # # # # @app.callback(Output("ipn-toast", "is_open"), Output("ipn-toast", "header"), Output("ipn-toast", "children"),
# # # # #               Output("ipn-toast", "icon"), Input("ipn-data-store", "data"), prevent_initial_call=True)
# # # # # def show_ipn_toast(data):
# # # # #     if not data: return False, "", "", ""
# # # # #     header, icon = "IPN: Transaction Complete", "warning" if data['failed'] > 0 else "success"
# # # # #     body = f"{data['coop']}: Paid {data['success']}/{data['total']} farmers. ({data['failed']} failed)"
# # # # #     return True, header, body, icon
# # # # #
# # # # #
# # # # # @app.callback(Output("coop-history-placeholder", "children"), Input("user-session", "data"),
# # # # #               Input("coop-alert", "is_open"), prevent_initial_call=False)
# # # # # def render_coop_history(session_data, alert_is_open):
# # # # #     if not session_data or session_data.get("role") != "cooperative": return None
# # # # #     conn = sqlite3.connect('capital_pay_simplified.db')
# # # # #     df = pd.read_sql_query(
# # # # #         "SELECT id, filename, status, admin_notes, submission_timestamp FROM submission_batches WHERE cooperative_id = ? ORDER BY submission_timestamp DESC",
# # # # #         conn, params=(session_data['id'],))
# # # # #     conn.close()
# # # # #     if df.empty: return dbc.Alert("No submissions yet.", color="info")
# # # # #     return dbc.Accordion([
# # # # #         dbc.AccordionItem([
# # # # #             html.P(
# # # # #                 f"Submitted on: {datetime.strptime(row['submission_timestamp'].split('.')[0], '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d %I:%M %p')}"),
# # # # #             dbc.Alert(f"Admin Note: {row['admin_notes']}", color="info") if row['admin_notes'] else "",
# # # # #             dbc.Button("View Results", id={'type': 'view-results-btn', 'index': row['id']}) if row[
# # # # #                                                                                                    'status'] == 'processed' else ""
# # # # #         ], title=html.Div([row['filename'], dbc.Badge(row['status'].replace('_', ' ').title(), className="ms-2",
# # # # #                                                       color="success" if row['status'] == 'processed' else "warning")]))
# # # # #         for _, row in df.iterrows()
# # # # #     ], start_collapsed=True)
# # # # #
# # # # #
# # # # # @app.callback(Output('coop-results-modal', 'is_open'), Output('coop-results-modal', 'children'),
# # # # #               Input({'type': 'view-results-btn', 'index': ALL}, 'n_clicks'), prevent_initial_call=True)
# # # # # def show_coop_results_modal(n_clicks):
# # # # #     if not any(n_clicks): return False, None
# # # # #     batch_id = int(eval(callback_context.triggered[0]['prop_id'].split('.')[0])['index'])
# # # # #     conn = sqlite3.connect('capital_pay_simplified.db')
# # # # #     df = pd.read_sql_query(
# # # # #         "SELECT farmer_name, bank_name, account_number, amount, status, failure_reason FROM farmer_payments WHERE batch_id = ?",
# # # # #         conn, params=(batch_id,))
# # # # #     conn.close()
# # # # #     return True, [
# # # # #         dbc.ModalHeader(f"Payment Results (Batch ID: {batch_id})"),
# # # # #         dbc.ModalBody(dash_table.DataTable(data=df.to_dict('records'),
# # # # #                                            columns=[{'name': i.replace('_', ' ').title(), 'id': i} for i in df.columns],
# # # # #                                            style_table={'overflowX': 'auto'}, editable=False,
# # # # #                                            style_data_conditional=[{'if': {'filter_query': '{status} = "paid"'},
# # # # #                                                                     'backgroundColor': '#d4edda'},
# # # # #                                                                    {'if': {'filter_query': '{status} = "failed"'},
# # # # #                                                                     'backgroundColor': '#f8d7da'}]))]
# # # # #
# # # # #
# # # # # @app.callback(Output("history-collapse", "is_open"), Input("toggle-history-btn", "n_clicks"),
# # # # #               State("history-collapse", "is_open"), prevent_initial_call=True)
# # # # # def toggle_history_collapse(n, is_open):
# # # # #     if n: return not is_open
# # # # #     return is_open
# # # # #
# # # # #
# # # # # @app.callback(Output("payment-history-placeholder", "children"), Input("history-collapse", "is_open"),
# # # # #               Input("ipn-data-store", "data"), prevent_initial_call=False)
# # # # # def render_payment_history(is_open, ipn_data):
# # # # #     if not is_open: return None
# # # # #     conn = sqlite3.connect('capital_pay_simplified.db')
# # # # #     df = pd.read_sql_query("SELECT * FROM payment_history ORDER BY processing_timestamp DESC", conn)
# # # # #     conn.close()
# # # # #     if df.empty: return dbc.Alert("No processed payments found.", color="secondary")
# # # # #     df['processing_timestamp'] = pd.to_datetime(df['processing_timestamp']).dt.strftime('%Y-%m-%d %I:%M:%S %p')
# # # # #     return dash_table.DataTable(data=df.to_dict('records'),
# # # # #                                 columns=[{'name': i.replace('_', ' ').title(), 'id': i} for i in df.columns],
# # # # #                                 page_size=10, style_table={'overflowX': 'auto'}, editable=False)
# # # # #
# # # # #
# # # # # @app.callback(Output("logs-collapse", "is_open"), Input("toggle-logs-btn", "n_clicks"),
# # # # #               State("logs-collapse", "is_open"), prevent_initial_call=True)
# # # # # def toggle_logs_collapse(n, is_open):
# # # # #     if n: return not is_open
# # # # #     return is_open
# # # # #
# # # # #
# # # # # @app.callback(Output("activity-logs-placeholder", "children"), Input("logs-collapse", "is_open"),
# # # # #               Input("ipn-data-store", "data"), prevent_initial_call=False)
# # # # # def render_activity_logs(is_open, ipn_data):
# # # # #     if not is_open: return None
# # # # #     conn = sqlite3.connect('capital_pay_simplified.db')
# # # # #     df = pd.read_sql_query(
# # # # #         "SELECT timestamp, cooperative_name, action, details FROM activity_logs ORDER BY timestamp DESC", conn)
# # # # #     conn.close()
# # # # #     if df.empty: return dbc.Alert("No user activity found.", color="secondary")
# # # # #     df['timestamp'] = pd.to_datetime(df['timestamp']).dt.strftime('%Y-%m-%d %I:%M:%S %p')
# # # # #     return dash_table.DataTable(data=df.to_dict('records'),
# # # # #                                 columns=[{'name': i.replace('_', ' ').title(), 'id': i} for i in df.columns],
# # # # #                                 page_size=10, style_table={'overflowX': 'auto'}, editable=False,
# # # # #                                 style_cell={'whiteSpace': 'normal', 'height': 'auto', 'textAlign': 'left'})
# # # # #
# # # # #
# # # # # # --- Run Application ---
# # # # # if __name__ == "__main__":
# # # # #     init_db()
# # # # #     app.run(debug=True, port=8075)
# # # # #
# # # #
# # # #
# # # # import dash
# # # # from dash import dcc, html, Input, Output, State, dash_table, callback_context, ALL
# # # # import dash_bootstrap_components as dbc
# # # # import pandas as pd
# # # # import sqlite3
# # # # import hashlib
# # # # from datetime import datetime
# # # # import base64
# # # # import io
# # # # import random
# # # # import json
# # # #
# # # # # Initialize Dash app
# # # # app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP], suppress_callback_exceptions=True)
# # # # app.title = "Capital Pay - Simplified Payment System"
# # # #
# # # #
# # # # # --- Database Setup ---
# # # # def init_db():
# # # #     conn = sqlite3.connect('capital_pay_simplified.db')
# # # #     cursor = conn.cursor()
# # # #
# # # #     # Users table
# # # #     cursor.execute('''
# # # #         CREATE TABLE IF NOT EXISTS users (
# # # #             id INTEGER PRIMARY KEY AUTOINCREMENT,
# # # #             username TEXT UNIQUE NOT NULL,
# # # #             password TEXT NOT NULL,
# # # #             role TEXT NOT NULL,
# # # #             cooperative_name TEXT
# # # #         )
# # # #     ''')
# # # #
# # # #     # Submission Batches table
# # # #     cursor.execute('''
# # # #         CREATE TABLE IF NOT EXISTS submission_batches (
# # # #             id INTEGER PRIMARY KEY AUTOINCREMENT,
# # # #             cooperative_id INTEGER,
# # # #             filename TEXT,
# # # #             record_count INTEGER,
# # # #             total_amount REAL,
# # # #             submission_timestamp TIMESTAMP,
# # # #             status TEXT,
# # # #             admin_notes TEXT,
# # # #             cooperative_notes TEXT,
# # # #             FOREIGN KEY (cooperative_id) REFERENCES users (id)
# # # #         )
# # # #     ''')
# # # #
# # # #     # Farmer Payments table
# # # #     cursor.execute('''
# # # #         CREATE TABLE IF NOT EXISTS farmer_payments (
# # # #             id INTEGER PRIMARY KEY AUTOINCREMENT,
# # # #             batch_id INTEGER,
# # # #             farmer_name TEXT NOT NULL,
# # # #             bank_name TEXT NOT NULL,
# # # #             account_number TEXT NOT NULL,
# # # #             amount REAL NOT NULL,
# # # #             status TEXT DEFAULT 'pending',
# # # #             failure_reason TEXT,
# # # #             FOREIGN KEY (batch_id) REFERENCES submission_batches (id)
# # # #         )
# # # #     ''')
# # # #
# # # #     # Payment History table
# # # #     cursor.execute('''
# # # #         CREATE TABLE IF NOT EXISTS payment_history (
# # # #             id INTEGER PRIMARY KEY AUTOINCREMENT,
# # # #             batch_id INTEGER,
# # # #             cooperative_name TEXT,
# # # #             filename TEXT,
# # # #             record_count INTEGER,
# # # #             total_amount REAL,
# # # #             processing_timestamp TIMESTAMP
# # # #         )
# # # #     ''')
# # # #
# # # #     # Activity Logs table
# # # #     cursor.execute('''
# # # #         CREATE TABLE IF NOT EXISTS activity_logs (
# # # #             id INTEGER PRIMARY KEY AUTOINCREMENT,
# # # #             timestamp TIMESTAMP,
# # # #             user_id INTEGER,
# # # #             cooperative_name TEXT,
# # # #             action TEXT,
# # # #             details TEXT,
# # # #             FOREIGN KEY (user_id) REFERENCES users (id)
# # # #         )
# # # #     ''')
# # # #
# # # #     # Pre-populate with default users if table is empty
# # # #     cursor.execute("SELECT COUNT(*) from users")
# # # #     if cursor.fetchone()[0] == 0:
# # # #         admin_password = hashlib.sha256("admin123".encode()).hexdigest()
# # # #         coop_password = hashlib.sha256("coop123".encode()).hexdigest()
# # # #         users_to_add = [
# # # #             ("admin", admin_password, "admin", "Capital Pay Admin"),
# # # #             ("kcu", coop_password, "cooperative", "Kilimanjaro Cooperative Union"),
# # # #             ("mbeyacof", coop_password, "cooperative", "Mbeya Coffee Union"),
# # # #             ("dodoma_coop", coop_password, "cooperative", "Dodoma Grain Cooperative"),
# # # #             ("tanga_coop", coop_password, "cooperative", "Tanga Sisal Cooperative"),
# # # #             ("iringa_coop", coop_password, "cooperative", "Iringa Maize Cooperative"),
# # # #             ("morogoro_coop", coop_password, "cooperative", "Morogoro Rice Cooperative"),
# # # #             ("ruvuma_coop", coop_password, "cooperative", "Ruvuma Cashew Cooperative")
# # # #         ]
# # # #         for user in users_to_add:
# # # #             cursor.execute(
# # # #                 "INSERT OR IGNORE INTO users (username, password, role, cooperative_name) VALUES (?, ?, ?, ?)", user)
# # # #
# # # #     conn.commit()
# # # #     conn.close()
# # # #
# # # #
# # # # # --- Utility Functions ---
# # # # def log_activity(user_id, action, details=""):
# # # #     conn = sqlite3.connect('capital_pay_simplified.db')
# # # #     cursor = conn.cursor()
# # # #     cursor.execute("SELECT cooperative_name FROM users WHERE id = ?", (user_id,))
# # # #     cooperative_name = cursor.fetchone()[0]
# # # #     cursor.execute(
# # # #         "INSERT INTO activity_logs (timestamp, user_id, cooperative_name, action, details) VALUES (?, ?, ?, ?, ?)",
# # # #         (datetime.now(), user_id, cooperative_name, action, details))
# # # #     conn.commit()
# # # #     conn.close()
# # # #
# # # #
# # # # def authenticate_user(username, password):
# # # #     conn = sqlite3.connect('capital_pay_simplified.db')
# # # #     cursor = conn.cursor()
# # # #     cursor.execute("SELECT id, password, role, cooperative_name FROM users WHERE username = ?", (username,))
# # # #     user = cursor.fetchone()
# # # #     conn.close()
# # # #     if user and user[1] == hashlib.sha256(password.encode()).hexdigest():
# # # #         return {"id": user[0], "username": username, "role": user[2], "cooperative_name": user[3]}
# # # #     return None
# # # #
# # # #
# # # # # --- Layout Definitions ---
# # # # def create_login_layout():
# # # #     return dbc.Container([
# # # #         dbc.Row(dbc.Col(dbc.Card([
# # # #             dbc.CardBody([
# # # #                 html.H2("Capital Pay", className="text-center mb-4 text-success"),
# # # #                 dbc.Input(id="login-username", placeholder="Username", type="text", className="mb-3"),
# # # #                 dbc.Input(id="login-password", placeholder="Password", type="password", className="mb-3"),
# # # #                 dbc.Button("Login", id="login-button", color="success", className="w-100"),
# # # #                 html.Div(id="login-alert-placeholder", className="mt-3")
# # # #             ])
# # # #         ], className="shadow"), width=10, sm=8, md=6, lg=4), justify="center",
# # # #             className="min-vh-100 align-items-center"),
# # # #         dbc.Alert([
# # # #             html.H5("Demo Credentials", className="alert-heading"),
# # # #             html.P([html.B("Admin: "), "username: ", html.Code("admin"), ", password: ", html.Code("admin123")]),
# # # #             html.P([html.B("Cooperatives: "), "Usernames are ", html.Code("kcu"), ", ", html.Code("mbeyacof"), ", ",
# # # #                     html.Code("tanga_coop"), ", etc."]),
# # # #             html.P([html.B("Password (all coops): "), html.Code("coop123")]),
# # # #         ], color="info", style={"position": "absolute", "bottom": "10px", "left": "10px", "width": "auto"})
# # # #     ], fluid=True, className="bg-light")
# # # #
# # # #
# # # # def create_cooperative_layout(session_data):
# # # #     return html.Div([
# # # #         dbc.NavbarSimple(brand=session_data.get('cooperative_name'),
# # # #                          children=[dbc.Button("Logout", id="logout-button", color="light", outline=True)],
# # # #                          color="success", dark=True),
# # # #         dbc.Container([
# # # #             dbc.Alert(id="coop-alert", is_open=False, duration=4000),
# # # #             html.H3("Farmer Data Submission  Portal", className="my-4"),
# # # #             dcc.Upload(id='upload-data', children=html.Div(['Drag and Drop or ', html.A('Select a CSV/Excel File')]),
# # # #                        style={'width': '100%', 'height': '60px', 'lineHeight': '60px', 'borderWidth': '1px',
# # # #                               'borderStyle': 'dashed', 'borderRadius': '5px', 'textAlign': 'center',
# # # #                               'margin': '10px 0'},
# # # #                        multiple=False),
# # # #             html.Hr(),
# # # #             html.Div(id="submission-table-placeholder"),
# # # #             html.Hr(),
# # # #             html.H3("Submission History", className="my-4"),
# # # #             html.Div(id="coop-history-placeholder"),
# # # #         ], fluid=True),
# # # #         dbc.Modal(id="coop-results-modal", size="xl", is_open=False)
# # # #     ])
# # # #
# # # #
# # # # def create_admin_layout(session_data):
# # # #     return html.Div([
# # # #         dbc.Toast(id="ipn-toast", is_open=False, duration=6000, icon="success",
# # # #                   style={"position": "fixed", "top": 20, "right": 20, "width": 350, "zIndex": 9999}),
# # # #         dbc.NavbarSimple(brand="Admin Payments Dashboard",
# # # #                          children=[dbc.Button("Logout", id="logout-button", color="light", outline=True)],
# # # #                          color="primary", dark=True),
# # # #         dbc.Container([
# # # #             html.Div(id="admin-dashboard-content"),
# # # #             html.Hr(),
# # # #             html.H3("Payment History", className="my-4"),
# # # #             dbc.Button("Show/Hide History", id="toggle-history-btn", className="mb-3"),
# # # #             dbc.Collapse(html.Div(id="payment-history-placeholder"), id="history-collapse", is_open=False),
# # # #             html.Hr(),
# # # #             html.H3("User Activity Logs", className="my-4"),
# # # #             dbc.Button("Show/Hide Logs", id="toggle-logs-btn", className="mb-3"),
# # # #             dbc.Collapse(html.Div(id="activity-logs-placeholder"), id="logs-collapse", is_open=False),
# # # #         ], fluid=True, className="py-4"),
# # # #         dbc.Modal(id="details-modal", size="xl", is_open=False),
# # # #         dbc.Modal([
# # # #             dbc.ModalHeader("Processing Payment"),
# # # #             dbc.ModalBody(id="payment-animation-placeholder"),
# # # #             dbc.ModalFooter(dbc.Button("Close", id="payment-close-button", color="secondary", disabled=True))
# # # #         ], id="payment-modal", backdrop="static")
# # # #     ])
# # # #
# # # #
# # # # # Main App Layout
# # # # app.layout = html.Div([
# # # #     dcc.Store(id="user-session", storage_type="session"),
# # # #     dcc.Store(id="batch-to-process"),
# # # #     dcc.Store(id='ipn-data-store'),
# # # #     dcc.Interval(id='payment-interval', interval=1500, n_intervals=0, disabled=True),
# # # #     dcc.Store(id='submission-trigger-store'),  # Used to refresh admin view on new submission
# # # #     html.Div(id="main-content")
# # # # ])
# # # #
# # # #
# # # # # --- Callbacks ---
# # # # @app.callback(
# # # #     Output("main-content", "children"),
# # # #     Input("user-session", "data")
# # # # )
# # # # def display_page(session_data):
# # # #     if session_data:
# # # #         if session_data.get("role") == "admin":
# # # #             return create_admin_layout(session_data)
# # # #         elif session_data.get("role") == "cooperative":
# # # #             return create_cooperative_layout(session_data)
# # # #     return create_login_layout()
# # # #
# # # #
# # # # @app.callback(
# # # #     Output("user-session", "data"),
# # # #     Output("login-alert-placeholder", "children"),
# # # #     Input("login-button", "n_clicks"),
# # # #     State("login-username", "value"),
# # # #     State("login-password", "value"),
# # # #     prevent_initial_call=True
# # # # )
# # # # def handle_login(n_clicks, username, password):
# # # #     if not username or not password: return dash.no_update, dbc.Alert("Fields cannot be empty.", color="warning")
# # # #     user = authenticate_user(username, password)
# # # #     if user:
# # # #         log_activity(user['id'], 'Login', f"User '{user['username']}' logged in.")
# # # #         return user, None
# # # #     return None, dbc.Alert("Invalid credentials.", color="danger")
# # # #
# # # #
# # # # @app.callback(
# # # #     Output("user-session", "data", allow_duplicate=True),
# # # #     Input("logout-button", "n_clicks"),
# # # #     prevent_initial_call=True
# # # # )
# # # # def handle_logout(n_clicks):
# # # #     if n_clicks: return None
# # # #     return dash.no_update
# # # #
# # # #
# # # # @app.callback(
# # # #     Output("submission-table-placeholder", "children"),
# # # #     Input('upload-data', 'contents'),
# # # #     State('upload-data', 'filename'),
# # # #     prevent_initial_call=True
# # # # )
# # # # def update_output(contents, filename):
# # # #     if contents is None: return html.Div()
# # # #     content_type, content_string = contents.split(',')
# # # #     decoded = base64.b64decode(content_string)
# # # #     try:
# # # #         df = pd.read_csv(io.StringIO(decoded.decode('utf-8'))) if 'csv' in filename else pd.read_excel(
# # # #             io.BytesIO(decoded))
# # # #         required_cols = {'farmer_name', 'bank_name', 'account_number', 'amount'}
# # # #         if not required_cols.issubset(df.columns): return dbc.Alert(
# # # #             f"File is missing columns: {required_cols - set(df.columns)}", color="danger")
# # # #         return html.Div([
# # # #             dcc.Store(id='submission-data', data={'df': df.to_dict('records'), 'filename': filename}),
# # # #             html.H5("Review Data"),
# # # #             dash_table.DataTable(id='editable-datatable', data=df.to_dict('records'),
# # # #                                  columns=[{'name': i, 'id': i} for i in df.columns], page_size=10,
# # # #                                  style_table={'overflowX': 'auto'}, editable=True),
# # # #             html.Hr(),
# # # #             dbc.Label("Note to Admin (Optional)", html_for="coop-note-textarea"),
# # # #             dbc.Textarea(id='coop-note-textarea', placeholder="Add notes for the admin regarding this submission...",
# # # #                          className="mb-3"),
# # # #             html.Div(dbc.Button("Submit to Admin", id="submit-to-admin-button", color="primary"),
# # # #                      className="d-flex justify-content-end")
# # # #         ])
# # # #     except Exception as e:
# # # #         return dbc.Alert(f"Error processing file: {e}", color="danger")
# # # #
# # # #
# # # # @app.callback(
# # # #     Output("coop-alert", "children"),
# # # #     Output("coop-alert", "is_open"),
# # # #     Output("coop-alert", "color"),
# # # #     Output("submission-table-placeholder", "children", allow_duplicate=True),
# # # #     Output("submission-trigger-store", "data"),
# # # #     Input("submit-to-admin-button", "n_clicks"),
# # # #     State("editable-datatable", "data"),
# # # #     State("submission-data", "data"),
# # # #     State("user-session", "data"),
# # # #     State("coop-note-textarea", "value"),
# # # #     prevent_initial_call=True
# # # # )
# # # # def submit_to_admin(n_clicks, table_data, submission_data_store, session_data, coop_note):
# # # #     if not n_clicks or not table_data: return "", False, "", dash.no_update, dash.no_update
# # # #     df = pd.DataFrame(table_data)
# # # #     filename = submission_data_store.get('filename', 'uploaded_file')
# # # #     conn = sqlite3.connect('capital_pay_simplified.db')
# # # #     cursor = conn.cursor()
# # # #     try:
# # # #         cursor.execute(
# # # #             "INSERT INTO submission_batches (cooperative_id, filename, record_count, total_amount, submission_timestamp, status, cooperative_notes) VALUES (?, ?, ?, ?, ?, ?, ?)",
# # # #             (session_data['id'], filename, len(df), df['amount'].sum(), datetime.now(), 'pending_approval', coop_note))
# # # #         batch_id = cursor.lastrowid
# # # #         df_to_db = df[['farmer_name', 'bank_name', 'account_number', 'amount']]
# # # #         df_to_db['batch_id'] = batch_id
# # # #         df_to_db.to_sql('farmer_payments', conn, if_exists='append', index=False)
# # # #         conn.commit()
# # # #         log_activity(session_data['id'], 'Data Submission', f"Submitted '{filename}' with {len(df)} records.")
# # # #         msg, color = f"Successfully submitted {len(df)} records.", "success"
# # # #         # Update the trigger store to signal a new submission for the admin dashboard
# # # #         return msg, True, color, html.Div(), datetime.now().isoformat()
# # # #     except Exception as e:
# # # #         conn.rollback()
# # # #         msg, color = f"Database error: {e}", "danger"
# # # #     finally:
# # # #         conn.close()
# # # #     return msg, True, color, dash.no_update, dash.no_update
# # # #
# # # #
# # # # @app.callback(
# # # #     Output("admin-dashboard-content", "children"),
# # # #     Input("user-session", "data"),
# # # #     Input("ipn-data-store", "data"),
# # # #     Input("submission-trigger-store", "data")
# # # # )
# # # # def render_admin_dashboard(session_data, ipn_data, submission_trigger):
# # # #     if not session_data or session_data.get("role") != "admin": return None
# # # #     conn = sqlite3.connect('capital_pay_simplified.db')
# # # #     query = "SELECT b.id, u.cooperative_name, b.filename, b.record_count, b.total_amount FROM submission_batches b JOIN users u ON b.cooperative_id = u.id WHERE b.status = 'pending_approval' ORDER BY b.submission_timestamp DESC"
# # # #     batches_df = pd.read_sql_query(query, conn)
# # # #     conn.close()
# # # #     if batches_df.empty: return dbc.Alert("No Pending Payments found.", color="info", className="m-4")
# # # #     cards = [dbc.Card([
# # # #         dbc.CardHeader(f"From: {row['cooperative_name']}"),
# # # #         dbc.CardBody([
# # # #             html.H5(row['filename'], className="card-title"),
# # # #             html.P(f"{row['record_count']} farmers, Total: TSH {row['total_amount']:,.2f}")
# # # #         ]),
# # # #         dbc.CardFooter(html.Div([
# # # #             dbc.Button("View Details", id={'type': 'view-details-btn', 'index': row['id']}, color="secondary"),
# # # #             dbc.Button("Pay Now", id={'type': 'pay-now-btn', 'index': row['id']}, color="success"),
# # # #         ], className="d-flex justify-content-between"))
# # # #     ], className="mb-3") for _, row in batches_df.iterrows()]
# # # #     return [html.H3("Pending Payments", className="mb-4")] + cards
# # # #
# # # #
# # # # @app.callback(
# # # #     Output("details-modal", "is_open"),
# # # #     Output("details-modal", "children"),
# # # #     Input({'type': 'view-details-btn', 'index': ALL}, 'n_clicks'),
# # # #     prevent_initial_call=True
# # # # )
# # # # def toggle_details_modal(n_clicks):
# # # #     if not any(n_clicks): return False, None
# # # #     batch_id = int(eval(callback_context.triggered[0]['prop_id'].split('.')[0])['index'])
# # # #     conn = sqlite3.connect('capital_pay_simplified.db')
# # # #     df = pd.read_sql_query(
# # # #         "SELECT farmer_name, bank_name, account_number, amount FROM farmer_payments WHERE batch_id = ?", conn,
# # # #         params=(batch_id,))
# # # #     notes_df = pd.read_sql_query("SELECT admin_notes, cooperative_notes FROM submission_batches WHERE id = ?", conn,
# # # #                                  params=(batch_id,))
# # # #     conn.close()
# # # #     admin_note, coop_note = notes_df['admin_notes'].iloc[0] or "", notes_df['cooperative_notes'].iloc[0]
# # # #     return True, [
# # # #         dbc.ModalHeader(f"Submission Details (Batch ID: {batch_id})"),
# # # #         dbc.ModalBody([
# # # #             dash_table.DataTable(data=df.to_dict('records'), columns=[{'name': i, 'id': i} for i in df.columns],
# # # #                                  style_table={'maxHeight': '40vh', 'overflowY': 'auto'}),
# # # #             html.Hr(),
# # # #             html.H5("Communication"),
# # # #             dbc.Label("Note from Cooperative:"),
# # # #             dbc.Alert(coop_note, color="info") if coop_note else html.P("No note provided.",
# # # #                                                                         className="text-muted fst-italic"),
# # # #             dbc.Label("Your Response to Cooperative:", className="mt-2"),
# # # #             dbc.Alert(id="note-save-alert", is_open=False, duration=3000),
# # # #             dcc.Textarea(id={'type': 'admin-note-textarea', 'index': batch_id}, value=admin_note,
# # # #                          style={'width': '100%', 'height': 100}),
# # # #             dbc.Button("Save Response", id={'type': 'save-note-btn', 'index': batch_id}, color="primary",
# # # #                        className="mt-2")
# # # #         ])
# # # #     ]
# # # #
# # # #
# # # # @app.callback(
# # # #     Output("note-save-alert", "is_open"),
# # # #     Output("note-save-alert", "children"),
# # # #     Output("note-save-alert", "color"),
# # # #     Input({'type': 'save-note-btn', 'index': ALL}, 'n_clicks'),
# # # #     State({'type': 'admin-note-textarea', 'index': ALL}, 'value'),
# # # #     prevent_initial_call=True
# # # # )
# # # # def save_admin_note(n_clicks, notes):
# # # #     if not any(n_clicks): return False, "", ""
# # # #     ctx = callback_context.triggered[0]
# # # #     batch_id = int(eval(ctx['prop_id'].split('.')[0])['index'])
# # # #     note_value = notes[0]
# # # #     try:
# # # #         conn = sqlite3.connect('capital_pay_simplified.db')
# # # #         cursor = conn.cursor()
# # # #         cursor.execute("UPDATE submission_batches SET admin_notes = ? WHERE id = ?", (note_value, batch_id))
# # # #         conn.commit()
# # # #         conn.close()
# # # #         return True, "Response saved successfully!", "success"
# # # #     except Exception as e:
# # # #         return True, f"Error saving response: {e}", "danger"
# # # #
# # # #
# # # # # --- FULLY FIXED PAYMENT CALLBACK ---
# # # # @app.callback(
# # # #     Output("payment-modal", "is_open"),
# # # #     Output("payment-interval", "disabled"),
# # # #     Output("payment-animation-placeholder", "children"),
# # # #     Output("payment-close-button", "disabled"),
# # # #     Output("batch-to-process", "data"),
# # # #     Output("ipn-data-store", "data"),
# # # #     Input({'type': 'pay-now-btn', 'index': ALL}, 'n_clicks'),
# # # #     Input("payment-interval", "n_intervals"),
# # # #     Input("payment-close-button", "n_clicks"),
# # # #     State("batch-to-process", "data"),
# # # #     State("user-session", "data"),
# # # #     prevent_initial_call=True
# # # # )
# # # # def handle_payment_processing(pay_clicks, n_intervals, close_clicks, batch_id, session_data):
# # # #     # This is the most robust way to check what triggered the callback.
# # # #     # It prevents any action from happening on page load.
# # # #     ctx = callback_context
# # # #     if not ctx.triggered:
# # # #         return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update
# # # #
# # # #     # Identify the component that fired the callback
# # # #     triggered_id_str = ctx.triggered[0]['prop_id']
# # # #     triggered_value = ctx.triggered[0]['value']
# # # #
# # # #     # --- TRIGGER 1: A "Pay Now" button was clicked ---
# # # #     # We check if the ID is a 'pay-now-btn' and if the value is not None (i.e., it was clicked)
# # # #     if 'pay-now-btn' in triggered_id_str and triggered_value is not None:
# # # #         # Extract the batch ID from the component's ID string
# # # #         id_dict = json.loads(triggered_id_str.split('.')[0])
# # # #         new_batch_id = id_dict['index']
# # # #
# # # #         animation_step = html.Div([
# # # #             html.Div("🔄", style={'fontSize': 50}),
# # # #             dbc.Progress(value=5),
# # # #             html.P("Initiating...")
# # # #         ], className="text-center")
# # # #         # Open modal, enable interval, show animation, disable close button, store batch id
# # # #         return True, False, animation_step, True, new_batch_id, dash.no_update
# # # #
# # # #     # --- TRIGGER 2: The interval timer is running ---
# # # #     elif 'payment-interval' in triggered_id_str and batch_id is not None:
# # # #         if n_intervals < 4:
# # # #             progress = (n_intervals + 1) * 25
# # # #             animation_step = html.Div([
# # # #                 html.Div("🔄", style={'fontSize': 50}),
# # # #                 dbc.Progress(value=progress, striped=True, animated=True),
# # # #                 html.P("Processing...")
# # # #             ], className="text-center")
# # # #             return True, False, animation_step, True, batch_id, dash.no_update
# # # #         else:
# # # #             # Final processing step
# # # #             conn = sqlite3.connect('capital_pay_simplified.db')
# # # #             cursor = conn.cursor()
# # # #             cursor.execute(
# # # #                 "SELECT u.cooperative_name, b.filename, b.record_count, b.total_amount FROM submission_batches b JOIN users u ON b.cooperative_id = u.id WHERE b.id = ?",
# # # #                 (batch_id,))
# # # #             batch_info = cursor.fetchone()
# # # #             # This UPDATE ensures the card disappears on the dashboard after processing
# # # #             cursor.execute("UPDATE submission_batches SET status = 'processed' WHERE id = ?", (batch_id,))
# # # #
# # # #             payments, success, failed = [], 0, 0
# # # #             reasons = ["Invalid Account", "Bank Error", "Name Mismatch"]
# # # #             cursor.execute("SELECT id FROM farmer_payments WHERE batch_id = ?", (batch_id,))
# # # #             for (pid,) in cursor.fetchall():
# # # #                 if random.random() < 0.95:
# # # #                     success += 1;
# # # #                     payments.append(('paid', None, pid))
# # # #                 else:
# # # #                     failed += 1;
# # # #                     payments.append(('failed', random.choice(reasons), pid))
# # # #             cursor.executemany("UPDATE farmer_payments SET status = ?, failure_reason = ? WHERE id = ?", payments)
# # # #
# # # #             if batch_info:
# # # #                 coop_name, filename, record_count, total_amount = batch_info
# # # #                 cursor.execute(
# # # #                     "INSERT INTO payment_history (batch_id, cooperative_name, filename, record_count, total_amount, processing_timestamp) VALUES (?, ?, ?, ?, ?, ?)",
# # # #                     (batch_id, coop_name, filename, record_count, total_amount, datetime.now()))
# # # #             conn.commit()
# # # #             conn.close()
# # # #
# # # #             log_activity(session_data['id'], 'Payment Processed',
# # # #                          f"Processed '{batch_info[1]}' for {batch_info[0]}. Success: {success}, Failed: {failed}.")
# # # #             # Updating ipn-data-store triggers the dashboard refresh
# # # #             ipn = {'coop': batch_info[0], 'success': success, 'failed': failed, 'total': batch_info[2]}
# # # #             result = html.Div([
# # # #                 html.Div("✅", style={'fontSize': 60, 'color': 'green'}),
# # # #                 dbc.Progress(value=100, color="success"),
# # # #                 html.H5("Payment Processed!")
# # # #             ], className="text-center")
# # # #             return True, True, result, False, None, ipn
# # # #
# # # #     # --- TRIGGER 3: The close button on the modal was clicked ---
# # # #     elif 'payment-close-button' in triggered_id_str:
# # # #         return False, True, "", True, None, dash.no_update
# # # #
# # # #     # If triggered by anything else, do nothing.
# # # #     return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update
# # # #
# # # #
# # # # @app.callback(
# # # #     Output("ipn-toast", "is_open"),
# # # #     Output("ipn-toast", "header"),
# # # #     Output("ipn-toast", "children"),
# # # #     Output("ipn-toast", "icon"),
# # # #     Input("ipn-data-store", "data"),
# # # #     prevent_initial_call=True
# # # # )
# # # # def show_ipn_toast(data):
# # # #     if not data: return False, "", "", ""
# # # #     header, icon = "IPN: Transaction Complete", "warning" if data['failed'] > 0 else "success"
# # # #     body = f"{data['coop']}: Paid {data['success']}/{data['total']} farmers. ({data['failed']} failed)"
# # # #     return True, header, body, icon
# # # #
# # # #
# # # # @app.callback(
# # # #     Output("coop-history-placeholder", "children"),
# # # #     Input("user-session", "data"),
# # # #     Input("coop-alert", "is_open")  # Refresh history after a successful submission
# # # # )
# # # # def render_coop_history(session_data, alert_is_open):
# # # #     if not session_data or session_data.get("role") != "cooperative": return None
# # # #     conn = sqlite3.connect('capital_pay_simplified.db')
# # # #     df = pd.read_sql_query(
# # # #         "SELECT id, filename, status, admin_notes, submission_timestamp FROM submission_batches WHERE cooperative_id = ? ORDER BY submission_timestamp DESC",
# # # #         conn, params=(session_data['id'],))
# # # #     conn.close()
# # # #     if df.empty: return dbc.Alert("No submissions yet.", color="info")
# # # #     return dbc.Accordion([
# # # #         dbc.AccordionItem([
# # # #             html.P(
# # # #                 f"Submitted on: {datetime.strptime(row['submission_timestamp'].split('.')[0], '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d %I:%M %p')}"),
# # # #             dbc.Alert(f"Admin Response: {row['admin_notes']}", color="info") if row['admin_notes'] else "",
# # # #             dbc.Button("View Results", id={'type': 'view-results-btn', 'index': row['id']}) if row[
# # # #                                                                                                    'status'] == 'processed' else ""
# # # #         ], title=html.Div([
# # # #             row['filename'],
# # # #             dbc.Badge(row['status'].replace('_', ' ').title(), className="ms-2",
# # # #                       color="success" if row['status'] == 'processed' else "warning")
# # # #         ]))
# # # #         for _, row in df.iterrows()
# # # #     ], start_collapsed=True)
# # # #
# # # #
# # # # @app.callback(
# # # #     Output('coop-results-modal', 'is_open'),
# # # #     Output('coop-results-modal', 'children'),
# # # #     Input({'type': 'view-results-btn', 'index': ALL}, 'n_clicks'),
# # # #     prevent_initial_call=True
# # # # )
# # # # def show_coop_results_modal(n_clicks):
# # # #     if not any(n_clicks): return False, None
# # # #     batch_id = int(eval(callback_context.triggered[0]['prop_id'].split('.')[0])['index'])
# # # #     conn = sqlite3.connect('capital_pay_simplified.db')
# # # #     df = pd.read_sql_query(
# # # #         "SELECT farmer_name, bank_name, account_number, amount, status, failure_reason FROM farmer_payments WHERE batch_id = ?",
# # # #         conn, params=(batch_id,))
# # # #     conn.close()
# # # #     return True, [
# # # #         dbc.ModalHeader(f"Payment Results (Batch ID: {batch_id})"),
# # # #         dbc.ModalBody(dash_table.DataTable(
# # # #             data=df.to_dict('records'),
# # # #             columns=[{'name': i.replace('_', ' ').title(), 'id': i} for i in df.columns],
# # # #             style_table={'overflowX': 'auto'},
# # # #             editable=False,
# # # #             style_data_conditional=[
# # # #                 {'if': {'filter_query': '{status} = "paid"'}, 'backgroundColor': '#d4edda'},
# # # #                 {'if': {'filter_query': '{status} = "failed"'}, 'backgroundColor': '#f8d7da'}
# # # #             ]
# # # #         ))
# # # #     ]
# # # #
# # # #
# # # # @app.callback(
# # # #     Output("history-collapse", "is_open"),
# # # #     Input("toggle-history-btn", "n_clicks"),
# # # #     State("history-collapse", "is_open"),
# # # #     prevent_initial_call=True
# # # # )
# # # # def toggle_history_collapse(n, is_open):
# # # #     if n: return not is_open
# # # #     return is_open
# # # #
# # # #
# # # # # --- PAYMENT HISTORY CALLBACK WITH COLOR-CODING ---
# # # # @app.callback(
# # # #     Output("payment-history-placeholder", "children"),
# # # #     Input("history-collapse", "is_open"),
# # # #     Input("ipn-data-store", "data")
# # # # )
# # # # def render_payment_history(is_open, ipn_data):
# # # #     if not is_open: return None
# # # #     conn = sqlite3.connect('capital_pay_simplified.db')
# # # #     df = pd.read_sql_query("SELECT * FROM payment_history ORDER BY processing_timestamp DESC", conn)
# # # #     conn.close()
# # # #     if df.empty: return dbc.Alert("No processed payments found.", color="secondary")
# # # #     df['processing_timestamp'] = pd.to_datetime(df['processing_timestamp']).dt.strftime('%Y-%m-%d %I:%M:%S %p')
# # # #
# # # #     # --- New logic for color coding ---
# # # #     cooperatives = sorted(df['cooperative_name'].unique())
# # # #     # A palette of light, pleasant colors for the rows
# # # #     colors = ['#E6E6FA', '#FFF0F5', '#F0FFF0', '#F5FFFA', '#F0F8FF', '#F8F8FF', '#FFF5EE', '#FAFAD2']
# # # #     color_map = {coop: colors[i % len(colors)] for i, coop in enumerate(cooperatives)}
# # # #
# # # #     style_data_conditional = [
# # # #         {
# # # #             'if': {'filter_query': f'{{cooperative_name}} = "{coop_name}"'},
# # # #             'backgroundColor': color
# # # #         } for coop_name, color in color_map.items()
# # # #     ]
# # # #     # --- End of new logic ---
# # # #
# # # #     return dash_table.DataTable(
# # # #         data=df.to_dict('records'),
# # # #         columns=[{'name': i.replace('_', ' ').title(), 'id': i} for i in df.columns],
# # # #         page_size=10,
# # # #         style_table={'overflowX': 'auto'},
# # # #         editable=False,
# # # #         style_data_conditional=style_data_conditional  # Apply the conditional styles
# # # #     )
# # # #
# # # #
# # # # @app.callback(
# # # #     Output("logs-collapse", "is_open"),
# # # #     Input("toggle-logs-btn", "n_clicks"),
# # # #     State("logs-collapse", "is_open"),
# # # #     prevent_initial_call=True
# # # # )
# # # # def toggle_logs_collapse(n, is_open):
# # # #     if n: return not is_open
# # # #     return is_open
# # # #
# # # #
# # # # @app.callback(
# # # #     Output("activity-logs-placeholder", "children"),
# # # #     Input("logs-collapse", "is_open"),
# # # #     Input("ipn-data-store", "data")
# # # # )
# # # # def render_activity_logs(is_open, ipn_data):
# # # #     if not is_open: return None
# # # #     conn = sqlite3.connect('capital_pay_simplified.db')
# # # #     df = pd.read_sql_query(
# # # #         "SELECT timestamp, cooperative_name, action, details FROM activity_logs ORDER BY timestamp DESC", conn)
# # # #     conn.close()
# # # #     if df.empty: return dbc.Alert("No user activity found.", color="secondary")
# # # #     df['timestamp'] = pd.to_datetime(df['timestamp']).dt.strftime('%Y-%m-%d %I:%M:%S %p')
# # # #     return dash_table.DataTable(
# # # #         data=df.to_dict('records'),
# # # #         columns=[{'name': i.replace('_', ' ').title(), 'id': i} for i in df.columns],
# # # #         page_size=10, style_table={'overflowX': 'auto'}, editable=False,
# # # #         style_cell={'whiteSpace': 'normal', 'height': 'auto', 'textAlign': 'left'}
# # # #     )
# # # #
# # # #
# # # # # --- Run Application ---
# # # # if __name__ == "__main__":
# # # #     init_db()
# # # #     app.run(debug=True, port=8055)
# # #
# # #
# # # import dash
# # # from dash import dcc, html, Input, Output, State, dash_table, callback_context, ALL
# # # import dash_bootstrap_components as dbc
# # # import pandas as pd
# # # import sqlite3
# # # import hashlib
# # # from datetime import datetime
# # # import base64
# # # import io
# # # import random
# # # import json
# # #
# # # # Initialize Dash app
# # # app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP], suppress_callback_exceptions=True)
# # # app.title = "Capital Pay - Simplified Payment System"
# # #
# # #
# # # # --- Database Setup ---
# # # def init_db():
# # #     conn = sqlite3.connect('capital_pay_simplified.db')
# # #     cursor = conn.cursor()
# # #
# # #     # Users table
# # #     cursor.execute('''
# # #         CREATE TABLE IF NOT EXISTS users (
# # #             id INTEGER PRIMARY KEY AUTOINCREMENT,
# # #             username TEXT UNIQUE NOT NULL,
# # #             password TEXT NOT NULL,
# # #             role TEXT NOT NULL,
# # #             cooperative_name TEXT
# # #         )
# # #     ''')
# # #
# # #     # Submission Batches table
# # #     cursor.execute('''
# # #         CREATE TABLE IF NOT EXISTS submission_batches (
# # #             id INTEGER PRIMARY KEY AUTOINCREMENT,
# # #             cooperative_id INTEGER,
# # #             filename TEXT,
# # #             record_count INTEGER,
# # #             total_amount REAL,
# # #             submission_timestamp TIMESTAMP,
# # #             status TEXT,
# # #             admin_notes TEXT,
# # #             cooperative_notes TEXT,
# # #             FOREIGN KEY (cooperative_id) REFERENCES users (id)
# # #         )
# # #     ''')
# # #
# # #     # Farmer Payments table
# # #     cursor.execute('''
# # #         CREATE TABLE IF NOT EXISTS farmer_payments (
# # #             id INTEGER PRIMARY KEY AUTOINCREMENT,
# # #             batch_id INTEGER,
# # #             farmer_name TEXT NOT NULL,
# # #             bank_name TEXT NOT NULL,
# # #             account_number TEXT NOT NULL,
# # #             amount REAL NOT NULL,
# # #             status TEXT DEFAULT 'pending',
# # #             failure_reason TEXT,
# # #             FOREIGN KEY (batch_id) REFERENCES submission_batches (id)
# # #         )
# # #     ''')
# # #
# # #     # Payment History table
# # #     cursor.execute('''
# # #         CREATE TABLE IF NOT EXISTS payment_history (
# # #             id INTEGER PRIMARY KEY AUTOINCREMENT,
# # #             batch_id INTEGER,
# # #             cooperative_name TEXT,
# # #             filename TEXT,
# # #             record_count INTEGER,
# # #             total_amount REAL,
# # #             processing_timestamp TIMESTAMP
# # #         )
# # #     ''')
# # #
# # #     # Activity Logs table
# # #     cursor.execute('''
# # #         CREATE TABLE IF NOT EXISTS activity_logs (
# # #             id INTEGER PRIMARY KEY AUTOINCREMENT,
# # #             timestamp TIMESTAMP,
# # #             user_id INTEGER,
# # #             cooperative_name TEXT,
# # #             action TEXT,
# # #             details TEXT,
# # #             FOREIGN KEY (user_id) REFERENCES users (id)
# # #         )
# # #     ''')
# # #
# # #     # Pre-populate with default users if table is empty
# # #     cursor.execute("SELECT COUNT(*) from users")
# # #     if cursor.fetchone()[0] == 0:
# # #         admin_password = hashlib.sha256("admin123".encode()).hexdigest()
# # #         coop_password = hashlib.sha256("coop123".encode()).hexdigest()
# # #         users_to_add = [
# # #             ("admin", admin_password, "admin", "Capital Pay Admin"),
# # #             ("kcu", coop_password, "cooperative", "Kilimanjaro Cooperative Union"),
# # #             ("mbeyacof", coop_password, "cooperative", "Mbeya Coffee Union"),
# # #             ("dodoma_coop", coop_password, "cooperative", "Dodoma Grain Cooperative"),
# # #             ("tanga_coop", coop_password, "cooperative", "Tanga Sisal Cooperative"),
# # #             ("iringa_coop", coop_password, "cooperative", "Iringa Maize Cooperative"),
# # #             ("morogoro_coop", coop_password, "cooperative", "Morogoro Rice Cooperative"),
# # #             ("ruvuma_coop", coop_password, "cooperative", "Ruvuma Cashew Cooperative")
# # #         ]
# # #         for user in users_to_add:
# # #             cursor.execute(
# # #                 "INSERT OR IGNORE INTO users (username, password, role, cooperative_name) VALUES (?, ?, ?, ?)", user)
# # #
# # #     conn.commit()
# # #     conn.close()
# # #
# # #
# # # # --- Utility Functions ---
# # # def log_activity(user_id, action, details=""):
# # #     conn = sqlite3.connect('capital_pay_simplified.db')
# # #     cursor = conn.cursor()
# # #     cursor.execute("SELECT cooperative_name FROM users WHERE id = ?", (user_id,))
# # #     cooperative_name = cursor.fetchone()[0]
# # #     cursor.execute(
# # #         "INSERT INTO activity_logs (timestamp, user_id, cooperative_name, action, details) VALUES (?, ?, ?, ?, ?)",
# # #         (datetime.now(), user_id, cooperative_name, action, details))
# # #     conn.commit()
# # #     conn.close()
# # #
# # #
# # # def authenticate_user(username, password):
# # #     conn = sqlite3.connect('capital_pay_simplified.db')
# # #     cursor = conn.cursor()
# # #     cursor.execute("SELECT id, password, role, cooperative_name FROM users WHERE username = ?", (username,))
# # #     user = cursor.fetchone()
# # #     conn.close()
# # #     if user and user[1] == hashlib.sha256(password.encode()).hexdigest():
# # #         return {"id": user[0], "username": username, "role": user[2], "cooperative_name": user[3]}
# # #     return None
# # #
# # #
# # # # --- Layout Definitions ---
# # # # --- THIS FUNCTION HAS BEEN UPDATED ---
# # # def create_login_layout():
# # #     return dbc.Container([
# # #         dbc.Row(dbc.Col(dbc.Card([
# # #             dbc.CardBody([
# # #                 html.H2("Capital Pay", className="text-center mb-4 text-success"),
# # #                 dbc.Input(id="login-username", placeholder="Username", type="text", className="mb-3"),
# # #                 dbc.Input(id="login-password", placeholder="Password", type="password", className="mb-3"),
# # #                 dbc.Button("Login", id="login-button", color="success", className="w-100"),
# # #                 html.Div(id="login-alert-placeholder", className="mt-3")
# # #             ])
# # #         ], className="shadow"), width=10, sm=8, md=6, lg=4), justify="center",
# # #             className="min-vh-100 align-items-center"),
# # #
# # #         # Updated alert with specific login combinations
# # #         dbc.Alert([
# # #             html.H5("Demo Credentials", className="alert-heading"),
# # #             html.P([html.B("Admin Account:")]),
# # #             html.Ul([
# # #                 html.Li(["Username: ", html.Code("admin"), " | Password: ", html.Code("admin123")])
# # #             ]),
# # #             html.P([html.B("Cooperative Accounts:")]),
# # #             html.Ul([
# # #                 html.Li(["Username: ", html.Code("kcu"), " | Password: ", html.Code("coop123")]),
# # #                 html.Li(["Username: ", html.Code("mbeyacof"), " | Password: ", html.Code("coop123")]),
# # #                 html.Li(["Username: ", html.Code("dodoma_coop"), " | Password: ", html.Code("coop123")]),
# # #                 html.Li(["Username: ", html.Code("tanga_coop"), " | Password: ", html.Code("coop123")]),
# # #                 html.Li(["Username: ", html.Code("iringa_coop"), " | Password: ", html.Code("coop123")]),
# # #             ])
# # #         ], color="info", style={"position": "absolute", "bottom": "10px", "left": "10px", "width": "auto"})
# # #     ], fluid=True, className="bg-light")
# # #
# # #
# # # def create_cooperative_layout(session_data):
# # #     return html.Div([
# # #         dbc.NavbarSimple(brand=session_data.get('cooperative_name'),
# # #                          children=[dbc.Button("Logout", id="logout-button", color="light", outline=True)],
# # #                          color="success", dark=True),
# # #         dbc.Container([
# # #             dbc.Alert(id="coop-alert", is_open=False, duration=4000),
# # #             html.H3("Farmer Data Submission  Portal", className="my-4"),
# # #             dcc.Upload(id='upload-data', children=html.Div(['Drag and Drop or ', html.A('Select a CSV/Excel File')]),
# # #                        style={'width': '100%', 'height': '60px', 'lineHeight': '60px', 'borderWidth': '1px',
# # #                               'borderStyle': 'dashed', 'borderRadius': '5px', 'textAlign': 'center',
# # #                               'margin': '10px 0'},
# # #                        multiple=False),
# # #             html.Hr(),
# # #             html.Div(id="submission-table-placeholder"),
# # #             html.Hr(),
# # #             html.H3("Submission History", className="my-4"),
# # #             html.Div(id="coop-history-placeholder"),
# # #         ], fluid=True),
# # #         dbc.Modal(id="coop-results-modal", size="xl", is_open=False)
# # #     ])
# # #
# # #
# # # def create_admin_layout(session_data):
# # #     return html.Div([
# # #         dbc.Toast(id="ipn-toast", is_open=False, duration=6000, icon="success",
# # #                   style={"position": "fixed", "top": 20, "right": 20, "width": 350, "zIndex": 9999}),
# # #         dbc.NavbarSimple(brand="Admin Payments Dashboard",
# # #                          children=[dbc.Button("Logout", id="logout-button", color="light", outline=True)],
# # #                          color="primary", dark=True),
# # #         dbc.Container([
# # #             html.Div(id="admin-dashboard-content"),
# # #             html.Hr(),
# # #             html.H3("Payment History", className="my-4"),
# # #             dbc.Button("Show/Hide History", id="toggle-history-btn", className="mb-3"),
# # #             dbc.Collapse(html.Div(id="payment-history-placeholder"), id="history-collapse", is_open=False),
# # #             html.Hr(),
# # #             html.H3("User Activity Logs", className="my-4"),
# # #             dbc.Button("Show/Hide Logs", id="toggle-logs-btn", className="mb-3"),
# # #             dbc.Collapse(html.Div(id="activity-logs-placeholder"), id="logs-collapse", is_open=False),
# # #         ], fluid=True, className="py-4"),
# # #         dbc.Modal(id="details-modal", size="xl", is_open=False),
# # #         dbc.Modal([
# # #             dbc.ModalHeader("Processing Payment"),
# # #             dbc.ModalBody(id="payment-animation-placeholder"),
# # #             dbc.ModalFooter(dbc.Button("Close", id="payment-close-button", color="secondary", disabled=True))
# # #         ], id="payment-modal", backdrop="static")
# # #     ])
# # #
# # #
# # # # Main App Layout
# # # app.layout = html.Div([
# # #     dcc.Store(id="user-session", storage_type="session"),
# # #     dcc.Store(id="batch-to-process"),
# # #     dcc.Store(id='ipn-data-store'),
# # #     dcc.Interval(id='payment-interval', interval=1500, n_intervals=0, disabled=True),
# # #     dcc.Store(id='submission-trigger-store'),  # Used to refresh admin view on new submission
# # #     html.Div(id="main-content")
# # # ])
# # #
# # #
# # # # --- Callbacks ---
# # # @app.callback(
# # #     Output("main-content", "children"),
# # #     Input("user-session", "data")
# # # )
# # # def display_page(session_data):
# # #     if session_data:
# # #         if session_data.get("role") == "admin":
# # #             return create_admin_layout(session_data)
# # #         elif session_data.get("role") == "cooperative":
# # #             return create_cooperative_layout(session_data)
# # #     return create_login_layout()
# # #
# # #
# # # @app.callback(
# # #     Output("user-session", "data"),
# # #     Output("login-alert-placeholder", "children"),
# # #     Input("login-button", "n_clicks"),
# # #     State("login-username", "value"),
# # #     State("login-password", "value"),
# # #     prevent_initial_call=True
# # # )
# # # def handle_login(n_clicks, username, password):
# # #     if not username or not password: return dash.no_update, dbc.Alert("Fields cannot be empty.", color="warning")
# # #     user = authenticate_user(username, password)
# # #     if user:
# # #         log_activity(user['id'], 'Login', f"User '{user['username']}' logged in.")
# # #         return user, None
# # #     return None, dbc.Alert("Invalid credentials.", color="danger")
# # #
# # #
# # # @app.callback(
# # #     Output("user-session", "data", allow_duplicate=True),
# # #     Input("logout-button", "n_clicks"),
# # #     prevent_initial_call=True
# # # )
# # # def handle_logout(n_clicks):
# # #     if n_clicks: return None
# # #     return dash.no_update
# # #
# # #
# # # @app.callback(
# # #     Output("submission-table-placeholder", "children"),
# # #     Input('upload-data', 'contents'),
# # #     State('upload-data', 'filename'),
# # #     prevent_initial_call=True
# # # )
# # # def update_output(contents, filename):
# # #     if contents is None: return html.Div()
# # #     content_type, content_string = contents.split(',')
# # #     decoded = base64.b64decode(content_string)
# # #     try:
# # #         df = pd.read_csv(io.StringIO(decoded.decode('utf-8'))) if 'csv' in filename else pd.read_excel(
# # #             io.BytesIO(decoded))
# # #         required_cols = {'farmer_name', 'bank_name', 'account_number', 'amount'}
# # #         if not required_cols.issubset(df.columns): return dbc.Alert(
# # #             f"File is missing columns: {required_cols - set(df.columns)}", color="danger")
# # #         return html.Div([
# # #             dcc.Store(id='submission-data', data={'df': df.to_dict('records'), 'filename': filename}),
# # #             html.H5("Review Data"),
# # #             dash_table.DataTable(id='editable-datatable', data=df.to_dict('records'),
# # #                                  columns=[{'name': i, 'id': i} for i in df.columns], page_size=10,
# # #                                  style_table={'overflowX': 'auto'}, editable=True),
# # #             html.Hr(),
# # #             dbc.Label("Note to Admin (Optional)", html_for="coop-note-textarea"),
# # #             dbc.Textarea(id='coop-note-textarea', placeholder="Add notes for the admin regarding this submission...",
# # #                          className="mb-3"),
# # #             html.Div(dbc.Button("Submit to Admin", id="submit-to-admin-button", color="primary"),
# # #                      className="d-flex justify-content-end")
# # #         ])
# # #     except Exception as e:
# # #         return dbc.Alert(f"Error processing file: {e}", color="danger")
# # #
# # #
# # # @app.callback(
# # #     Output("coop-alert", "children"),
# # #     Output("coop-alert", "is_open"),
# # #     Output("coop-alert", "color"),
# # #     Output("submission-table-placeholder", "children", allow_duplicate=True),
# # #     Output("submission-trigger-store", "data"),
# # #     Input("submit-to-admin-button", "n_clicks"),
# # #     State("editable-datatable", "data"),
# # #     State("submission-data", "data"),
# # #     State("user-session", "data"),
# # #     State("coop-note-textarea", "value"),
# # #     prevent_initial_call=True
# # # )
# # # def submit_to_admin(n_clicks, table_data, submission_data_store, session_data, coop_note):
# # #     if not n_clicks or not table_data: return "", False, "", dash.no_update, dash.no_update
# # #     df = pd.DataFrame(table_data)
# # #     filename = submission_data_store.get('filename', 'uploaded_file')
# # #     conn = sqlite3.connect('capital_pay_simplified.db')
# # #     cursor = conn.cursor()
# # #     try:
# # #         cursor.execute(
# # #             "INSERT INTO submission_batches (cooperative_id, filename, record_count, total_amount, submission_timestamp, status, cooperative_notes) VALUES (?, ?, ?, ?, ?, ?, ?)",
# # #             (session_data['id'], filename, len(df), df['amount'].sum(), datetime.now(), 'pending_approval', coop_note))
# # #         batch_id = cursor.lastrowid
# # #         df_to_db = df[['farmer_name', 'bank_name', 'account_number', 'amount']]
# # #         df_to_db['batch_id'] = batch_id
# # #         df_to_db.to_sql('farmer_payments', conn, if_exists='append', index=False)
# # #         conn.commit()
# # #         log_activity(session_data['id'], 'Data Submission', f"Submitted '{filename}' with {len(df)} records.")
# # #         msg, color = f"Successfully submitted {len(df)} records.", "success"
# # #         # Update the trigger store to signal a new submission for the admin dashboard
# # #         return msg, True, color, html.Div(), datetime.now().isoformat()
# # #     except Exception as e:
# # #         conn.rollback()
# # #         msg, color = f"Database error: {e}", "danger"
# # #     finally:
# # #         conn.close()
# # #     return msg, True, color, dash.no_update, dash.no_update
# # #
# # #
# # # @app.callback(
# # #     Output("admin-dashboard-content", "children"),
# # #     Input("user-session", "data"),
# # #     Input("ipn-data-store", "data"),
# # #     Input("submission-trigger-store", "data")
# # # )
# # # def render_admin_dashboard(session_data, ipn_data, submission_trigger):
# # #     if not session_data or session_data.get("role") != "admin": return None
# # #     conn = sqlite3.connect('capital_pay_simplified.db')
# # #     query = "SELECT b.id, u.cooperative_name, b.filename, b.record_count, b.total_amount FROM submission_batches b JOIN users u ON b.cooperative_id = u.id WHERE b.status = 'pending_approval' ORDER BY b.submission_timestamp DESC"
# # #     batches_df = pd.read_sql_query(query, conn)
# # #     conn.close()
# # #     if batches_df.empty: return dbc.Alert("No Pending Payments found.", color="info", className="m-4")
# # #     cards = [dbc.Card([
# # #         dbc.CardHeader(f"From: {row['cooperative_name']}"),
# # #         dbc.CardBody([
# # #             html.H5(row['filename'], className="card-title"),
# # #             html.P(f"{row['record_count']} farmers, Total: TSH {row['total_amount']:,.2f}")
# # #         ]),
# # #         dbc.CardFooter(html.Div([
# # #             dbc.Button("View Details", id={'type': 'view-details-btn', 'index': row['id']}, color="secondary"),
# # #             dbc.Button("Pay Now", id={'type': 'pay-now-btn', 'index': row['id']}, color="success"),
# # #         ], className="d-flex justify-content-between"))
# # #     ], className="mb-3") for _, row in batches_df.iterrows()]
# # #     return [html.H3("Pending Payments", className="mb-4")] + cards
# # #
# # #
# # # @app.callback(
# # #     Output("details-modal", "is_open"),
# # #     Output("details-modal", "children"),
# # #     Input({'type': 'view-details-btn', 'index': ALL}, 'n_clicks'),
# # #     prevent_initial_call=True
# # # )
# # # def toggle_details_modal(n_clicks):
# # #     if not any(n_clicks): return False, None
# # #     batch_id = int(eval(callback_context.triggered[0]['prop_id'].split('.')[0])['index'])
# # #     conn = sqlite3.connect('capital_pay_simplified.db')
# # #     df = pd.read_sql_query(
# # #         "SELECT farmer_name, bank_name, account_number, amount FROM farmer_payments WHERE batch_id = ?", conn,
# # #         params=(batch_id,))
# # #     notes_df = pd.read_sql_query("SELECT admin_notes, cooperative_notes FROM submission_batches WHERE id = ?", conn,
# # #                                  params=(batch_id,))
# # #     conn.close()
# # #     admin_note, coop_note = notes_df['admin_notes'].iloc[0] or "", notes_df['cooperative_notes'].iloc[0]
# # #     return True, [
# # #         dbc.ModalHeader(f"Submission Details (Batch ID: {batch_id})"),
# # #         dbc.ModalBody([
# # #             dash_table.DataTable(data=df.to_dict('records'), columns=[{'name': i, 'id': i} for i in df.columns],
# # #                                  style_table={'maxHeight': '40vh', 'overflowY': 'auto'}),
# # #             html.Hr(),
# # #             html.H5("Communication"),
# # #             dbc.Label("Note from Cooperative:"),
# # #             dbc.Alert(coop_note, color="info") if coop_note else html.P("No note provided.",
# # #                                                                         className="text-muted fst-italic"),
# # #             dbc.Label("Your Response to Cooperative:", className="mt-2"),
# # #             dbc.Alert(id="note-save-alert", is_open=False, duration=3000),
# # #             dcc.Textarea(id={'type': 'admin-note-textarea', 'index': batch_id}, value=admin_note,
# # #                          style={'width': '100%', 'height': 100}),
# # #             dbc.Button("Save Response", id={'type': 'save-note-btn', 'index': batch_id}, color="primary",
# # #                        className="mt-2")
# # #         ])
# # #     ]
# # #
# # #
# # # @app.callback(
# # #     Output("note-save-alert", "is_open"),
# # #     Output("note-save-alert", "children"),
# # #     Output("note-save-alert", "color"),
# # #     Input({'type': 'save-note-btn', 'index': ALL}, 'n_clicks'),
# # #     State({'type': 'admin-note-textarea', 'index': ALL}, 'value'),
# # #     prevent_initial_call=True
# # # )
# # # def save_admin_note(n_clicks, notes):
# # #     if not any(n_clicks): return False, "", ""
# # #     ctx = callback_context.triggered[0]
# # #     batch_id = int(eval(ctx['prop_id'].split('.')[0])['index'])
# # #     note_value = notes[0]
# # #     try:
# # #         conn = sqlite3.connect('capital_pay_simplified.db')
# # #         cursor = conn.cursor()
# # #         cursor.execute("UPDATE submission_batches SET admin_notes = ? WHERE id = ?", (note_value, batch_id))
# # #         conn.commit()
# # #         conn.close()
# # #         return True, "Response saved successfully!", "success"
# # #     except Exception as e:
# # #         return True, f"Error saving response: {e}", "danger"
# # #
# # #
# # # @app.callback(
# # #     Output("payment-modal", "is_open"),
# # #     Output("payment-interval", "disabled"),
# # #     Output("payment-animation-placeholder", "children"),
# # #     Output("payment-close-button", "disabled"),
# # #     Output("batch-to-process", "data"),
# # #     Output("ipn-data-store", "data"),
# # #     Input({'type': 'pay-now-btn', 'index': ALL}, 'n_clicks'),
# # #     Input("payment-interval", "n_intervals"),
# # #     Input("payment-close-button", "n_clicks"),
# # #     State("batch-to-process", "data"),
# # #     State("user-session", "data"),
# # #     prevent_initial_call=True
# # # )
# # # def handle_payment_processing(pay_clicks, n_intervals, close_clicks, batch_id, session_data):
# # #     ctx = callback_context
# # #     if not ctx.triggered:
# # #         return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update
# # #
# # #     triggered_id_str = ctx.triggered[0]['prop_id']
# # #     triggered_value = ctx.triggered[0]['value']
# # #
# # #     if 'pay-now-btn' in triggered_id_str and triggered_value is not None:
# # #         id_dict = json.loads(triggered_id_str.split('.')[0])
# # #         new_batch_id = id_dict['index']
# # #
# # #         animation_step = html.Div([
# # #             html.Div("🔄", style={'fontSize': 50}),
# # #             dbc.Progress(value=5),
# # #             html.P("Initiating...")
# # #         ], className="text-center")
# # #         return True, False, animation_step, True, new_batch_id, dash.no_update
# # #
# # #     elif 'payment-interval' in triggered_id_str and batch_id is not None:
# # #         if n_intervals < 4:
# # #             progress = (n_intervals + 1) * 25
# # #             animation_step = html.Div([
# # #                 html.Div("🔄", style={'fontSize': 50}),
# # #                 dbc.Progress(value=progress, striped=True, animated=True),
# # #                 html.P("Processing...")
# # #             ], className="text-center")
# # #             return True, False, animation_step, True, batch_id, dash.no_update
# # #         else:
# # #             conn = sqlite3.connect('capital_pay_simplified.db')
# # #             cursor = conn.cursor()
# # #             cursor.execute(
# # #                 "SELECT u.cooperative_name, b.filename, b.record_count, b.total_amount FROM submission_batches b JOIN users u ON b.cooperative_id = u.id WHERE b.id = ?",
# # #                 (batch_id,))
# # #             batch_info = cursor.fetchone()
# # #             cursor.execute("UPDATE submission_batches SET status = 'processed' WHERE id = ?", (batch_id,))
# # #
# # #             payments, success, failed = [], 0, 0
# # #             reasons = ["Invalid Account", "Bank Error", "Name Mismatch"]
# # #             cursor.execute("SELECT id FROM farmer_payments WHERE batch_id = ?", (batch_id,))
# # #             for (pid,) in cursor.fetchall():
# # #                 if random.random() < 0.95:
# # #                     success += 1;
# # #                     payments.append(('paid', None, pid))
# # #                 else:
# # #                     failed += 1;
# # #                     payments.append(('failed', random.choice(reasons), pid))
# # #             cursor.executemany("UPDATE farmer_payments SET status = ?, failure_reason = ? WHERE id = ?", payments)
# # #
# # #             if batch_info:
# # #                 coop_name, filename, record_count, total_amount = batch_info
# # #                 cursor.execute(
# # #                     "INSERT INTO payment_history (batch_id, cooperative_name, filename, record_count, total_amount, processing_timestamp) VALUES (?, ?, ?, ?, ?, ?)",
# # #                     (batch_id, coop_name, filename, record_count, total_amount, datetime.now()))
# # #             conn.commit()
# # #             conn.close()
# # #
# # #             log_activity(session_data['id'], 'Payment Processed',
# # #                          f"Processed '{batch_info[1]}' for {batch_info[0]}. Success: {success}, Failed: {failed}.")
# # #             ipn = {'coop': batch_info[0], 'success': success, 'failed': failed, 'total': batch_info[2]}
# # #             result = html.Div([
# # #                 html.Div("✅", style={'fontSize': 60, 'color': 'green'}),
# # #                 dbc.Progress(value=100, color="success"),
# # #                 html.H5("Payment Processed!")
# # #             ], className="text-center")
# # #             return True, True, result, False, None, ipn
# # #
# # #     elif 'payment-close-button' in triggered_id_str:
# # #         return False, True, "", True, None, dash.no_update
# # #
# # #     return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update
# # #
# # #
# # # @app.callback(
# # #     Output("ipn-toast", "is_open"),
# # #     Output("ipn-toast", "header"),
# # #     Output("ipn-toast", "children"),
# # #     Output("ipn-toast", "icon"),
# # #     Input("ipn-data-store", "data"),
# # #     prevent_initial_call=True
# # # )
# # # def show_ipn_toast(data):
# # #     if not data: return False, "", "", ""
# # #     header, icon = "IPN: Transaction Complete", "warning" if data['failed'] > 0 else "success"
# # #     body = f"{data['coop']}: Paid {data['success']}/{data['total']} farmers. ({data['failed']} failed)"
# # #     return True, header, body, icon
# # #
# # #
# # # @app.callback(
# # #     Output("coop-history-placeholder", "children"),
# # #     Input("user-session", "data"),
# # #     Input("coop-alert", "is_open")
# # # )
# # # def render_coop_history(session_data, alert_is_open):
# # #     if not session_data or session_data.get("role") != "cooperative": return None
# # #     conn = sqlite3.connect('capital_pay_simplified.db')
# # #     df = pd.read_sql_query(
# # #         "SELECT id, filename, status, admin_notes, submission_timestamp FROM submission_batches WHERE cooperative_id = ? ORDER BY submission_timestamp DESC",
# # #         conn, params=(session_data['id'],))
# # #     conn.close()
# # #     if df.empty: return dbc.Alert("No submissions yet.", color="info")
# # #     return dbc.Accordion([
# # #         dbc.AccordionItem([
# # #             html.P(
# # #                 f"Submitted on: {datetime.strptime(row['submission_timestamp'].split('.')[0], '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d %I:%M %p')}"),
# # #             dbc.Alert(f"Admin Response: {row['admin_notes']}", color="info") if row['admin_notes'] else "",
# # #             dbc.Button("View Results", id={'type': 'view-results-btn', 'index': row['id']}) if row[
# # #                                                                                                    'status'] == 'processed' else ""
# # #         ], title=html.Div([
# # #             row['filename'],
# # #             dbc.Badge(row['status'].replace('_', ' ').title(), className="ms-2",
# # #                       color="success" if row['status'] == 'processed' else "warning")
# # #         ]))
# # #         for _, row in df.iterrows()
# # #     ], start_collapsed=True)
# # #
# # #
# # # @app.callback(
# # #     Output('coop-results-modal', 'is_open'),
# # #     Output('coop-results-modal', 'children'),
# # #     Input({'type': 'view-results-btn', 'index': ALL}, 'n_clicks'),
# # #     prevent_initial_call=True
# # # )
# # # def show_coop_results_modal(n_clicks):
# # #     if not any(n_clicks): return False, None
# # #     batch_id = int(eval(callback_context.triggered[0]['prop_id'].split('.')[0])['index'])
# # #     conn = sqlite3.connect('capital_pay_simplified.db')
# # #     df = pd.read_sql_query(
# # #         "SELECT farmer_name, bank_name, account_number, amount, status, failure_reason FROM farmer_payments WHERE batch_id = ?",
# # #         conn, params=(batch_id,))
# # #     conn.close()
# # #     return True, [
# # #         dbc.ModalHeader(f"Payment Results (Batch ID: {batch_id})"),
# # #         dbc.ModalBody(dash_table.DataTable(
# # #             data=df.to_dict('records'),
# # #             columns=[{'name': i.replace('_', ' ').title(), 'id': i} for i in df.columns],
# # #             style_table={'overflowX': 'auto'},
# # #             editable=False,
# # #             style_data_conditional=[
# # #                 {'if': {'filter_query': '{status} = "paid"'}, 'backgroundColor': '#d4edda'},
# # #                 {'if': {'filter_query': '{status} = "failed"'}, 'backgroundColor': '#f8d7da'}
# # #             ]
# # #         ))
# # #     ]
# # #
# # #
# # # @app.callback(
# # #     Output("history-collapse", "is_open"),
# # #     Input("toggle-history-btn", "n_clicks"),
# # #     State("history-collapse", "is_open"),
# # #     prevent_initial_call=True
# # # )
# # # def toggle_history_collapse(n, is_open):
# # #     if n: return not is_open
# # #     return is_open
# # #
# # #
# # # @app.callback(
# # #     Output("payment-history-placeholder", "children"),
# # #     Input("history-collapse", "is_open"),
# # #     Input("ipn-data-store", "data")
# # # )
# # # def render_payment_history(is_open, ipn_data):
# # #     if not is_open: return None
# # #     conn = sqlite3.connect('capital_pay_simplified.db')
# # #     df = pd.read_sql_query("SELECT * FROM payment_history ORDER BY processing_timestamp DESC", conn)
# # #     conn.close()
# # #     if df.empty: return dbc.Alert("No processed payments found.", color="secondary")
# # #     df['processing_timestamp'] = pd.to_datetime(df['processing_timestamp']).dt.strftime('%Y-%m-%d %I:%M:%S %p')
# # #
# # #     cooperatives = sorted(df['cooperative_name'].unique())
# # #     colors = ['#E6E6FA', '#FFF0F5', '#F0FFF0', '#F5FFFA', '#F0F8FF', '#F8F8FF', '#FFF5EE', '#FAFAD2']
# # #     color_map = {coop: colors[i % len(colors)] for i, coop in enumerate(cooperatives)}
# # #
# # #     style_data_conditional = [
# # #         {
# # #             'if': {'filter_query': f'{{cooperative_name}} = "{coop_name}"'},
# # #             'backgroundColor': color
# # #         } for coop_name, color in color_map.items()
# # #     ]
# # #
# # #     return dash_table.DataTable(
# # #         data=df.to_dict('records'),
# # #         columns=[{'name': i.replace('_', ' ').title(), 'id': i} for i in df.columns],
# # #         page_size=10,
# # #         style_table={'overflowX': 'auto'},
# # #         editable=False,
# # #         style_data_conditional=style_data_conditional
# # #     )
# # #
# # #
# # # @app.callback(
# # #     Output("logs-collapse", "is_open"),
# # #     Input("toggle-logs-btn", "n_clicks"),
# # #     State("logs-collapse", "is_open"),
# # #     prevent_initial_call=True
# # # )
# # # def toggle_logs_collapse(n, is_open):
# # #     if n: return not is_open
# # #     return is_open
# # #
# # #
# # # @app.callback(
# # #     Output("activity-logs-placeholder", "children"),
# # #     Input("logs-collapse", "is_open"),
# # #     Input("ipn-data-store", "data")
# # # )
# # # def render_activity_logs(is_open, ipn_data):
# # #     if not is_open: return None
# # #     conn = sqlite3.connect('capital_pay_simplified.db')
# # #     df = pd.read_sql_query(
# # #         "SELECT timestamp, cooperative_name, action, details FROM activity_logs ORDER BY timestamp DESC", conn)
# # #     conn.close()
# # #     if df.empty: return dbc.Alert("No user activity found.", color="secondary")
# # #     df['timestamp'] = pd.to_datetime(df['timestamp']).dt.strftime('%Y-%m-%d %I:%M:%S %p')
# # #     return dash_table.DataTable(
# # #         data=df.to_dict('records'),
# # #         columns=[{'name': i.replace('_', ' ').title(), 'id': i} for i in df.columns],
# # #         page_size=10, style_table={'overflowX': 'auto'}, editable=False,
# # #         style_cell={'whiteSpace': 'normal', 'height': 'auto', 'textAlign': 'left'}
# # #     )
# # #
# # #
# # # # --- Run Application ---
# # # if __name__ == "__main__":
# # #     init_db()
# # #     app.run(debug=True, port=8015)
# #
# #
# # import dash
# # from dash import dcc, html, Input, Output, State, dash_table, callback_context, ALL
# # import dash_bootstrap_components as dbc
# # import pandas as pd
# # import sqlite3
# # import hashlib
# # from datetime import datetime
# # import base64
# # import io
# # import random
# # import json
# #
# # # Initialize Dash app
# # app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP], suppress_callback_exceptions=True)
# # app.title = "Farmers Payment Module - Simplified Payment System"
# #
# #
# # # --- Database Setup ---
# # def init_db():
# #     conn = sqlite3.connect('farmers_payment_module.db')
# #     cursor = conn.cursor()
# #
# #     # Users table
# #     cursor.execute('''
# #         CREATE TABLE IF NOT EXISTS users (
# #             id INTEGER PRIMARY KEY AUTOINCREMENT,
# #             username TEXT UNIQUE NOT NULL,
# #             password TEXT NOT NULL,
# #             role TEXT NOT NULL,
# #             cooperative_name TEXT
# #         )
# #     ''')
# #
# #     # Submission Batches table
# #     cursor.execute('''
# #         CREATE TABLE IF NOT EXISTS submission_batches (
# #             id INTEGER PRIMARY KEY AUTOINCREMENT,
# #             cooperative_id INTEGER,
# #             filename TEXT,
# #             record_count INTEGER,
# #             total_amount REAL,
# #             submission_timestamp TIMESTAMP,
# #             status TEXT,
# #             admin_notes TEXT,
# #             cooperative_notes TEXT,
# #             FOREIGN KEY (cooperative_id) REFERENCES users (id)
# #         )
# #     ''')
# #
# #     # Farmer Payments table
# #     cursor.execute('''
# #         CREATE TABLE IF NOT EXISTS farmer_payments (
# #             id INTEGER PRIMARY KEY AUTOINCREMENT,
# #             batch_id INTEGER,
# #             farmer_name TEXT NOT NULL,
# #             bank_name TEXT NOT NULL,
# #             account_number TEXT NOT NULL,
# #             amount REAL NOT NULL,
# #             status TEXT DEFAULT 'pending',
# #             failure_reason TEXT,
# #             FOREIGN KEY (batch_id) REFERENCES submission_batches (id)
# #         )
# #     ''')
# #
# #     # Payment History table
# #     cursor.execute('''
# #         CREATE TABLE IF NOT EXISTS payment_history (
# #             id INTEGER PRIMARY KEY AUTOINCREMENT,
# #             batch_id INTEGER,
# #             cooperative_name TEXT,
# #             filename TEXT,
# #             record_count INTEGER,
# #             total_amount REAL,
# #             processing_timestamp TIMESTAMP
# #         )
# #     ''')
# #
# #     # Activity Logs table
# #     cursor.execute('''
# #         CREATE TABLE IF NOT EXISTS activity_logs (
# #             id INTEGER PRIMARY KEY AUTOINCREMENT,
# #             timestamp TIMESTAMP,
# #             user_id INTEGER,
# #             cooperative_name TEXT,
# #             action TEXT,
# #             details TEXT,
# #             FOREIGN KEY (user_id) REFERENCES users (id)
# #         )
# #     ''')
# #
# #     # Pre-populate with default users if table is empty
# #     cursor.execute("SELECT COUNT(*) from users")
# #     if cursor.fetchone()[0] == 0:
# #         admin_password = hashlib.sha256("admin123".encode()).hexdigest()
# #         coop_password = hashlib.sha256("coop123".encode()).hexdigest()
# #         users_to_add = [
# #             ("admin", admin_password, "admin", "Farmers Payment Module Admin"),
# #             ("kcu", coop_password, "cooperative", "Kilimanjaro Cooperative Union"),
# #             ("mbeyacof", coop_password, "cooperative", "Mbeya Coffee Union"),
# #             ("dodoma_coop", coop_password, "cooperative", "Dodoma Grain Cooperative"),
# #             ("tanga_coop", coop_password, "cooperative", "Tanga Sisal Cooperative"),
# #             ("iringa_coop", coop_password, "cooperative", "Iringa Maize Cooperative"),
# #             ("morogoro_coop", coop_password, "cooperative", "Morogoro Rice Cooperative"),
# #             ("ruvuma_coop", coop_password, "cooperative", "Ruvuma Cashew Cooperative")
# #         ]
# #         for user in users_to_add:
# #             cursor.execute(
# #                 "INSERT OR IGNORE INTO users (username, password, role, cooperative_name) VALUES (?, ?, ?, ?)", user)
# #
# #     conn.commit()
# #     conn.close()
# #
# #
# # # --- Utility Functions ---
# # def log_activity(user_id, action, details=""):
# #     conn = sqlite3.connect('farmers_payment_module.db')
# #     cursor = conn.cursor()
# #     cursor.execute("SELECT cooperative_name FROM users WHERE id = ?", (user_id,))
# #     cooperative_name = cursor.fetchone()[0]
# #     cursor.execute(
# #         "INSERT INTO activity_logs (timestamp, user_id, cooperative_name, action, details) VALUES (?, ?, ?, ?, ?)",
# #         (datetime.now(), user_id, cooperative_name, action, details))
# #     conn.commit()
# #     conn.close()
# #
# #
# # def authenticate_user(username, password):
# #     conn = sqlite3.connect('farmers_payment_module.db')
# #     cursor = conn.cursor()
# #     cursor.execute("SELECT id, password, role, cooperative_name FROM users WHERE username = ?", (username,))
# #     user = cursor.fetchone()
# #     conn.close()
# #     if user and user[1] == hashlib.sha256(password.encode()).hexdigest():
# #         return {"id": user[0], "username": username, "role": user[2], "cooperative_name": user[3]}
# #     return None
# #
# #
# # # --- Layout Definitions ---
# # def create_login_layout():
# #     return dbc.Container([
# #         dbc.Row(dbc.Col(dbc.Card([
# #             dbc.CardBody([
# #                 html.H2("Farmers Payment Module", className="text-center mb-4 text-success"),
# #                 dbc.Input(id="login-username", placeholder="Username", type="text", className="mb-3"),
# #                 dbc.Input(id="login-password", placeholder="Password", type="password", className="mb-3"),
# #                 dbc.Button("Login", id="login-button", color="success", className="w-100"),
# #                 html.Div(id="login-alert-placeholder", className="mt-3")
# #             ])
# #         ], className="shadow"), width=10, sm=8, md=6, lg=4), justify="center",
# #             className="min-vh-100 align-items-center"),
# #
# #         dbc.Alert([
# #             html.H5("Demo Credentials", className="alert-heading"),
# #             html.P([html.B("Admin Account:")]),
# #             html.Ul([
# #                 html.Li(["Username: ", html.Code("admin"), " | Password: ", html.Code("admin123")])
# #             ]),
# #             html.P([html.B("Cooperative Accounts:")]),
# #             html.Ul([
# #                 html.Li(["Username: ", html.Code("kcu"), " | Password: ", html.Code("coop123")]),
# #                 html.Li(["Username: ", html.Code("mbeyacof"), " | Password: ", html.Code("coop123")]),
# #                 html.Li(["Username: ", html.Code("dodoma_coop"), " | Password: ", html.Code("coop123")]),
# #                 html.Li(["Username: ", html.Code("tanga_coop"), " | Password: ", html.Code("coop123")]),
# #                 html.Li(["Username: ", html.Code("iringa_coop"), " | Password: ", html.Code("coop123")]),
# #             ])
# #         ], color="info", style={"position": "absolute", "bottom": "10px", "left": "10px", "width": "auto"})
# #     ], fluid=True, className="bg-light")
# #
# #
# # def create_cooperative_layout(session_data):
# #     return html.Div([
# #         dbc.NavbarSimple(brand=session_data.get('cooperative_name'),
# #                          children=[dbc.Button("Logout", id="logout-button", color="light", outline=True)],
# #                          color="success", dark=True),
# #         dbc.Container([
# #             dbc.Alert(id="coop-alert", is_open=False, duration=4000),
# #             html.H3("Farmer Data Submission  Portal", className="my-4"),
# #             dcc.Upload(id='upload-data', children=html.Div(['Drag and Drop or ', html.A('Select a CSV/Excel File')]),
# #                        style={'width': '100%', 'height': '60px', 'lineHeight': '60px', 'borderWidth': '1px',
# #                               'borderStyle': 'dashed', 'borderRadius': '5px', 'textAlign': 'center',
# #                               'margin': '10px 0'},
# #                        multiple=False),
# #             html.Hr(),
# #             html.Div(id="submission-table-placeholder"),
# #             html.Hr(),
# #             html.H3("Submission History", className="my-4"),
# #             html.Div(id="coop-history-placeholder"),
# #         ], fluid=True),
# #         dbc.Modal(id="coop-results-modal", size="xl", is_open=False)
# #     ])
# #
# #
# # def create_admin_layout(session_data):
# #     return html.Div([
# #         dbc.Toast(id="ipn-toast", is_open=False, duration=6000, icon="success",
# #                   style={"position": "fixed", "top": 20, "right": 20, "width": 350, "zIndex": 9999}),
# #         dbc.NavbarSimple(brand="Admin Payments Dashboard",
# #                          children=[dbc.Button("Logout", id="logout-button", color="light", outline=True)],
# #                          color="primary", dark=True),
# #         dbc.Container([
# #             html.Div(id="kpi-cards-placeholder"),  # Placeholder for KPIs and new TMX card
# #
# #             html.Div(id="admin-dashboard-content"),
# #             html.Hr(),
# #
# #             html.H3("Master Payment Data (Single Source of Truth)", className="my-4"),
# #             dbc.Button("Show/Hide Master Data", id="toggle-master-data-btn", className="mb-3"),
# #             dbc.Collapse(html.Div(id="master-data-placeholder"), id="master-data-collapse", is_open=False),
# #             html.Hr(),
# #
# #             html.H3("Payment History", className="my-4"),
# #             dbc.Button("Show/Hide History", id="toggle-history-btn", className="mb-3"),
# #             dbc.Collapse(html.Div(id="payment-history-placeholder"), id="history-collapse", is_open=False),
# #             html.Hr(),
# #
# #             html.H3("User Activity Logs", className="my-4"),
# #             dbc.Button("Show/Hide Logs", id="toggle-logs-btn", className="mb-3"),
# #             dbc.Collapse(html.Div(id="activity-logs-placeholder"), id="logs-collapse", is_open=False),
# #         ], fluid=True, className="py-4"),
# #         dbc.Modal(id="details-modal", size="xl", is_open=False),
# #         dbc.Modal([
# #             dbc.ModalHeader("Processing Payment"),
# #             dbc.ModalBody(id="payment-animation-placeholder"),
# #             dbc.ModalFooter(dbc.Button("Close", id="payment-close-button", color="secondary", disabled=True))
# #         ], id="payment-modal", backdrop="static")
# #     ])
# #
# #
# # # Main App Layout
# # app.layout = html.Div([
# #     dcc.Store(id="user-session", storage_type="session"),
# #     dcc.Store(id="batch-to-process"),
# #     dcc.Store(id='ipn-data-store'),
# #     dcc.Interval(id='payment-interval', interval=1500, n_intervals=0, disabled=True),
# #     dcc.Store(id='submission-trigger-store'),
# #     html.Div(id="main-content")
# # ])
# #
# #
# # # --- Callbacks ---
# #
# # # --- THIS CALLBACK HAS BEEN UPDATED ---
# # @app.callback(
# #     Output("kpi-cards-placeholder", "children"),
# #     Input("user-session", "data"),
# #     Input("ipn-data-store", "data"),
# #     Input("submission-trigger-store", "data")
# # )
# # def update_kpi_cards(session_data, ipn_data, submission_trigger):
# #     if not session_data or session_data.get("role") != "admin":
# #         return None
# #
# #     conn = sqlite3.connect('farmers_payment_module.db')
# #     cursor = conn.cursor()
# #
# #     # TMX Funds Required calculation
# #     cursor.execute("SELECT SUM(total_amount), COUNT(id) FROM submission_batches WHERE status = 'pending_approval'")
# #     tmx_result = cursor.fetchone()
# #     tmx_amount_needed = tmx_result[0] or 0
# #     pending_coop_count = tmx_result[1] or 0
# #
# #     # KPI 1: Total Amount Paid
# #     cursor.execute("SELECT SUM(amount) FROM farmer_payments WHERE status = 'paid'")
# #     total_paid = cursor.fetchone()[0] or 0
# #
# #     # KPI 2: Total Farmers Paid
# #     cursor.execute("SELECT COUNT(id) FROM farmer_payments WHERE status = 'paid'")
# #     farmers_paid_count = cursor.fetchone()[0] or 0
# #
# #     # KPI 3: Pending Payments (already calculated for TMX)
# #     pending_submissions = pending_coop_count
# #
# #     # KPI 4: Number of Cooperatives
# #     cursor.execute("SELECT COUNT(id) FROM users WHERE role = 'cooperative'")
# #     coop_count = cursor.fetchone()[0] or 0
# #
# #     conn.close()
# #
# #     tmx_card = dbc.Card(
# #         dbc.CardBody([
# #             html.P("Funds Required from TMX", className="card-text text-muted small"),
# #             html.H3(f"TSH {tmx_amount_needed:,.2f}", className="card-title text-primary"),
# #             html.P(f"To clear {pending_coop_count} pending submission(s) as of {datetime.now().strftime('%Y-%m-%d')}",
# #                    className="card-text"),
# #         ]),
# #         className="mb-4",
# #         style={"border-left": "5px solid #0d6efd"}
# #     )
# #
# #     kpi_cards = dbc.Row([
# #         dbc.Col(dbc.Card(dbc.CardBody([
# #             html.H4(f"TSH {total_paid:,.2f}", className="card-title"),
# #             html.P("Total Amount Paid", className="card-text text-muted"),
# #         ])), width=6, lg=3, className="mb-3"),
# #         dbc.Col(dbc.Card(dbc.CardBody([
# #             html.H4(f"{farmers_paid_count:,}", className="card-title"),
# #             html.P("Total Farmers Paid", className="card-text text-muted"),
# #         ])), width=6, lg=3, className="mb-3"),
# #         dbc.Col(dbc.Card(dbc.CardBody([
# #             html.H4(pending_submissions, className="card-title text-warning"),
# #             html.P("Pending Payments", className="card-text text-muted"),
# #         ])), width=6, lg=3, className="mb-3"),
# #         dbc.Col(dbc.Card(dbc.CardBody([
# #             html.H4(coop_count, className="card-title"),
# #             html.P("Active Cooperatives", className="card-text text-muted"),
# #         ])), width=6, lg=3, className="mb-3"),
# #     ])
# #
# #     return html.Div([tmx_card, kpi_cards])
# #
# #
# # @app.callback(
# #     Output("main-content", "children"),
# #     Input("user-session", "data")
# # )
# # def display_page(session_data):
# #     if session_data:
# #         if session_data.get("role") == "admin":
# #             return create_admin_layout(session_data)
# #         elif session_data.get("role") == "cooperative":
# #             return create_cooperative_layout(session_data)
# #     return create_login_layout()
# #
# #
# # @app.callback(
# #     Output("user-session", "data"),
# #     Output("login-alert-placeholder", "children"),
# #     Input("login-button", "n_clicks"),
# #     State("login-username", "value"),
# #     State("login-password", "value"),
# #     prevent_initial_call=True
# # )
# # def handle_login(n_clicks, username, password):
# #     if not username or not password: return dash.no_update, dbc.Alert("Fields cannot be empty.", color="warning")
# #     user = authenticate_user(username, password)
# #     if user:
# #         log_activity(user['id'], 'Login', f"User '{user['username']}' logged in.")
# #         return user, None
# #     return None, dbc.Alert("Invalid credentials.", color="danger")
# #
# #
# # @app.callback(
# #     Output("user-session", "data", allow_duplicate=True),
# #     Input("logout-button", "n_clicks"),
# #     prevent_initial_call=True
# # )
# # def handle_logout(n_clicks):
# #     if n_clicks: return None
# #     return dash.no_update
# #
# #
# # @app.callback(
# #     Output("submission-table-placeholder", "children"),
# #     Input('upload-data', 'contents'),
# #     State('upload-data', 'filename'),
# #     prevent_initial_call=True
# # )
# # def update_output(contents, filename):
# #     if contents is None: return html.Div()
# #     content_type, content_string = contents.split(',')
# #     decoded = base64.b64decode(content_string)
# #     try:
# #         df = pd.read_csv(io.StringIO(decoded.decode('utf-8'))) if 'csv' in filename else pd.read_excel(
# #             io.BytesIO(decoded))
# #         required_cols = {'farmer_name', 'bank_name', 'account_number', 'amount'}
# #         if not required_cols.issubset(df.columns): return dbc.Alert(
# #             f"File is missing columns: {required_cols - set(df.columns)}", color="danger")
# #         return html.Div([
# #             dcc.Store(id='submission-data', data={'df': df.to_dict('records'), 'filename': filename}),
# #             html.H5("Review Data"),
# #             dash_table.DataTable(id='editable-datatable', data=df.to_dict('records'),
# #                                  columns=[{'name': i, 'id': i} for i in df.columns], page_size=10,
# #                                  style_table={'overflowX': 'auto'}, editable=True),
# #             html.Hr(),
# #             dbc.Label("Note to Admin (Optional)", html_for="coop-note-textarea"),
# #             dbc.Textarea(id='coop-note-textarea', placeholder="Add notes for the admin regarding this submission...",
# #                          className="mb-3"),
# #             html.Div(dbc.Button("Submit to Admin", id="submit-to-admin-button", color="primary"),
# #                      className="d-flex justify-content-end")
# #         ])
# #     except Exception as e:
# #         return dbc.Alert(f"Error processing file: {e}", color="danger")
# #
# #
# # @app.callback(
# #     Output("coop-alert", "children"),
# #     Output("coop-alert", "is_open"),
# #     Output("coop-alert", "color"),
# #     Output("submission-table-placeholder", "children", allow_duplicate=True),
# #     Output("submission-trigger-store", "data"),
# #     Input("submit-to-admin-button", "n_clicks"),
# #     State("editable-datatable", "data"),
# #     State("submission-data", "data"),
# #     State("user-session", "data"),
# #     State("coop-note-textarea", "value"),
# #     prevent_initial_call=True
# # )
# # def submit_to_admin(n_clicks, table_data, submission_data_store, session_data, coop_note):
# #     if not n_clicks or not table_data: return "", False, "", dash.no_update, dash.no_update
# #     df = pd.DataFrame(table_data)
# #     filename = submission_data_store.get('filename', 'uploaded_file')
# #     conn = sqlite3.connect('farmers_payment_module.db')
# #     cursor = conn.cursor()
# #     try:
# #         cursor.execute(
# #             "INSERT INTO submission_batches (cooperative_id, filename, record_count, total_amount, submission_timestamp, status, cooperative_notes) VALUES (?, ?, ?, ?, ?, ?, ?)",
# #             (session_data['id'], filename, len(df), df['amount'].sum(), datetime.now(), 'pending_approval', coop_note))
# #         batch_id = cursor.lastrowid
# #         df_to_db = df[['farmer_name', 'bank_name', 'account_number', 'amount']]
# #         df_to_db['batch_id'] = batch_id
# #         df_to_db.to_sql('farmer_payments', conn, if_exists='append', index=False)
# #         conn.commit()
# #         log_activity(session_data['id'], 'Data Submission', f"Submitted '{filename}' with {len(df)} records.")
# #         msg, color = f"Successfully submitted {len(df)} records.", "success"
# #         return msg, True, color, html.Div(), datetime.now().isoformat()
# #     except Exception as e:
# #         conn.rollback()
# #         msg, color = f"Database error: {e}", "danger"
# #     finally:
# #         conn.close()
# #     return msg, True, color, dash.no_update, dash.no_update
# #
# #
# # @app.callback(
# #     Output("admin-dashboard-content", "children"),
# #     Input("user-session", "data"),
# #     Input("ipn-data-store", "data"),
# #     Input("submission-trigger-store", "data")
# # )
# # def render_admin_dashboard(session_data, ipn_data, submission_trigger):
# #     if not session_data or session_data.get("role") != "admin": return None
# #     conn = sqlite3.connect('farmers_payment_module.db')
# #     query = "SELECT b.id, u.cooperative_name, b.filename, b.record_count, b.total_amount FROM submission_batches b JOIN users u ON b.cooperative_id = u.id WHERE b.status = 'pending_approval' ORDER BY b.submission_timestamp DESC"
# #     batches_df = pd.read_sql_query(query, conn)
# #     conn.close()
# #     if batches_df.empty: return dbc.Alert("No Pending Payments found.", color="info", className="m-4")
# #     cards = [dbc.Card([
# #         dbc.CardHeader(f"From: {row['cooperative_name']}"),
# #         dbc.CardBody([
# #             html.H5(row['filename'], className="card-title"),
# #             html.P(f"{row['record_count']} farmers, Total: TSH {row['total_amount']:,.2f}")
# #         ]),
# #         dbc.CardFooter(html.Div([
# #             dbc.Button("View Details", id={'type': 'view-details-btn', 'index': row['id']}, color="secondary"),
# #             dbc.Button("Pay Now", id={'type': 'pay-now-btn', 'index': row['id']}, color="success"),
# #         ], className="d-flex justify-content-between"))
# #     ], className="mb-3") for _, row in batches_df.iterrows()]
# #     return [html.H3("Pending Payments", className="mb-4")] + cards
# #
# #
# # @app.callback(
# #     Output("details-modal", "is_open"),
# #     Output("details-modal", "children"),
# #     Input({'type': 'view-details-btn', 'index': ALL}, 'n_clicks'),
# #     prevent_initial_call=True
# # )
# # def toggle_details_modal(n_clicks):
# #     if not any(n_clicks): return False, None
# #     batch_id = int(eval(callback_context.triggered[0]['prop_id'].split('.')[0])['index'])
# #     conn = sqlite3.connect('farmers_payment_module.db')
# #     df = pd.read_sql_query(
# #         "SELECT farmer_name, bank_name, account_number, amount FROM farmer_payments WHERE batch_id = ?", conn,
# #         params=(batch_id,))
# #     notes_df = pd.read_sql_query("SELECT admin_notes, cooperative_notes FROM submission_batches WHERE id = ?", conn,
# #                                  params=(batch_id,))
# #     conn.close()
# #     admin_note, coop_note = notes_df['admin_notes'].iloc[0] or "", notes_df['cooperative_notes'].iloc[0]
# #     return True, [
# #         dbc.ModalHeader(f"Submission Details (Batch ID: {batch_id})"),
# #         dbc.ModalBody([
# #             dash_table.DataTable(data=df.to_dict('records'), columns=[{'name': i, 'id': i} for i in df.columns],
# #                                  style_table={'maxHeight': '40vh', 'overflowY': 'auto'}),
# #             html.Hr(),
# #             html.H5("Communication"),
# #             dbc.Label("Note from Cooperative:"),
# #             dbc.Alert(coop_note, color="info") if coop_note else html.P("No note provided.",
# #                                                                         className="text-muted fst-italic"),
# #             dbc.Label("Your Response to Cooperative:", className="mt-2"),
# #             dbc.Alert(id="note-save-alert", is_open=False, duration=3000),
# #             dcc.Textarea(id={'type': 'admin-note-textarea', 'index': batch_id}, value=admin_note,
# #                          style={'width': '100%', 'height': 100}),
# #             dbc.Button("Save Response", id={'type': 'save-note-btn', 'index': batch_id}, color="primary",
# #                        className="mt-2")
# #         ])
# #     ]
# #
# #
# # @app.callback(
# #     Output("note-save-alert", "is_open"),
# #     Output("note-save-alert", "children"),
# #     Output("note-save-alert", "color"),
# #     Input({'type': 'save-note-btn', 'index': ALL}, 'n_clicks'),
# #     State({'type': 'admin-note-textarea', 'index': ALL}, 'value'),
# #     prevent_initial_call=True
# # )
# # def save_admin_note(n_clicks, notes):
# #     if not any(n_clicks): return False, "", ""
# #     ctx = callback_context.triggered[0]
# #     batch_id = int(eval(ctx['prop_id'].split('.')[0])['index'])
# #     note_value = notes[0]
# #     try:
# #         conn = sqlite3.connect('farmers_payment_module.db')
# #         cursor = conn.cursor()
# #         cursor.execute("UPDATE submission_batches SET admin_notes = ? WHERE id = ?", (note_value, batch_id))
# #         conn.commit()
# #         conn.close()
# #         return True, "Response saved successfully!", "success"
# #     except Exception as e:
# #         return True, f"Error saving response: {e}", "danger"
# #
# #
# # @app.callback(
# #     Output("payment-modal", "is_open"),
# #     Output("payment-interval", "disabled"),
# #     Output("payment-animation-placeholder", "children"),
# #     Output("payment-close-button", "disabled"),
# #     Output("batch-to-process", "data"),
# #     Output("ipn-data-store", "data"),
# #     Input({'type': 'pay-now-btn', 'index': ALL}, 'n_clicks'),
# #     Input("payment-interval", "n_intervals"),
# #     Input("payment-close-button", "n_clicks"),
# #     State("batch-to-process", "data"),
# #     State("user-session", "data"),
# #     prevent_initial_call=True
# # )
# # def handle_payment_processing(pay_clicks, n_intervals, close_clicks, batch_id, session_data):
# #     ctx = callback_context
# #     if not ctx.triggered:
# #         return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update
# #
# #     triggered_id_str = ctx.triggered[0]['prop_id']
# #     triggered_value = ctx.triggered[0]['value']
# #
# #     if 'pay-now-btn' in triggered_id_str and triggered_value is not None:
# #         id_dict = json.loads(triggered_id_str.split('.')[0])
# #         new_batch_id = id_dict['index']
# #
# #         animation_step = html.Div([
# #             html.Div("🔄", style={'fontSize': 50}),
# #             dbc.Progress(value=5),
# #             html.P("Initiating...")
# #         ], className="text-center")
# #         return True, False, animation_step, True, new_batch_id, dash.no_update
# #
# #     elif 'payment-interval' in triggered_id_str and batch_id is not None:
# #         if n_intervals < 4:
# #             progress = (n_intervals + 1) * 25
# #             animation_step = html.Div([
# #                 html.Div("🔄", style={'fontSize': 50}),
# #                 dbc.Progress(value=progress, striped=True, animated=True),
# #                 html.P("Processing...")
# #             ], className="text-center")
# #             return True, False, animation_step, True, batch_id, dash.no_update
# #         else:
# #             conn = sqlite3.connect('farmers_payment_module.db')
# #             cursor = conn.cursor()
# #             cursor.execute(
# #                 "SELECT u.cooperative_name, b.filename, b.record_count, b.total_amount FROM submission_batches b JOIN users u ON b.cooperative_id = u.id WHERE b.id = ?",
# #                 (batch_id,))
# #             batch_info = cursor.fetchone()
# #             cursor.execute("UPDATE submission_batches SET status = 'processed' WHERE id = ?", (batch_id,))
# #
# #             payments, success, failed = [], 0, 0
# #             reasons = ["Invalid Account", "Bank Error", "Name Mismatch"]
# #             cursor.execute("SELECT id FROM farmer_payments WHERE batch_id = ?", (batch_id,))
# #             for (pid,) in cursor.fetchall():
# #                 if random.random() < 0.95:
# #                     success += 1;
# #                     payments.append(('paid', None, pid))
# #                 else:
# #                     failed += 1;
# #                     payments.append(('failed', random.choice(reasons), pid))
# #             cursor.executemany("UPDATE farmer_payments SET status = ?, failure_reason = ? WHERE id = ?", payments)
# #
# #             if batch_info:
# #                 coop_name, filename, record_count, total_amount = batch_info
# #                 cursor.execute(
# #                     "INSERT INTO payment_history (batch_id, cooperative_name, filename, record_count, total_amount, processing_timestamp) VALUES (?, ?, ?, ?, ?, ?)",
# #                     (batch_id, coop_name, filename, record_count, total_amount, datetime.now()))
# #             conn.commit()
# #             conn.close()
# #
# #             log_activity(session_data['id'], 'Payment Processed',
# #                          f"Processed '{batch_info[1]}' for {batch_info[0]}. Success: {success}, Failed: {failed}.")
# #             ipn = {'coop': batch_info[0], 'success': success, 'failed': failed, 'total': batch_info[2]}
# #             result = html.Div([
# #                 html.Div("✅", style={'fontSize': 60, 'color': 'green'}),
# #                 dbc.Progress(value=100, color="success"),
# #                 html.H5("Payment Processed!")
# #             ], className="text-center")
# #             return True, True, result, False, None, ipn
# #
# #     elif 'payment-close-button' in triggered_id_str:
# #         return False, True, "", True, None, dash.no_update
# #
# #     return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update
# #
# #
# # @app.callback(
# #     Output("ipn-toast", "is_open"),
# #     Output("ipn-toast", "header"),
# #     Output("ipn-toast", "children"),
# #     Output("ipn-toast", "icon"),
# #     Input("ipn-data-store", "data"),
# #     prevent_initial_call=True
# # )
# # def show_ipn_toast(data):
# #     if not data: return False, "", "", ""
# #     header, icon = "IPN: Transaction Complete", "warning" if data['failed'] > 0 else "success"
# #     body = f"{data['coop']}: Paid {data['success']}/{data['total']} farmers. ({data['failed']} failed)"
# #     return True, header, body, icon
# #
# #
# # @app.callback(
# #     Output("coop-history-placeholder", "children"),
# #     Input("user-session", "data"),
# #     Input("coop-alert", "is_open")
# # )
# # def render_coop_history(session_data, alert_is_open):
# #     if not session_data or session_data.get("role") != "cooperative": return None
# #     conn = sqlite3.connect('farmers_payment_module.db')
# #     df = pd.read_sql_query(
# #         "SELECT id, filename, status, admin_notes, submission_timestamp FROM submission_batches WHERE cooperative_id = ? ORDER BY submission_timestamp DESC",
# #         conn, params=(session_data['id'],))
# #     conn.close()
# #     if df.empty: return dbc.Alert("No submissions yet.", color="info")
# #     return dbc.Accordion([
# #         dbc.AccordionItem([
# #             html.P(
# #                 f"Submitted on: {datetime.strptime(row['submission_timestamp'].split('.')[0], '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d %I:%M %p')}"),
# #             dbc.Alert(f"Admin Response: {row['admin_notes']}", color="info") if row['admin_notes'] else "",
# #             dbc.Button("View Results", id={'type': 'view-results-btn', 'index': row['id']}) if row[
# #                                                                                                    'status'] == 'processed' else ""
# #         ], title=html.Div([
# #             row['filename'],
# #             dbc.Badge(row['status'].replace('_', ' ').title(), className="ms-2",
# #                       color="success" if row['status'] == 'processed' else "warning")
# #         ]))
# #         for _, row in df.iterrows()
# #     ], start_collapsed=True)
# #
# #
# # @app.callback(
# #     Output('coop-results-modal', 'is_open'),
# #     Output('coop-results-modal', 'children'),
# #     Input({'type': 'view-results-btn', 'index': ALL}, 'n_clicks'),
# #     prevent_initial_call=True
# # )
# # def show_coop_results_modal(n_clicks):
# #     if not any(n_clicks): return False, None
# #     batch_id = int(eval(callback_context.triggered[0]['prop_id'].split('.')[0])['index'])
# #     conn = sqlite3.connect('farmers_payment_module.db')
# #     df = pd.read_sql_query(
# #         "SELECT farmer_name, bank_name, account_number, amount, status, failure_reason FROM farmer_payments WHERE batch_id = ?",
# #         conn, params=(batch_id,))
# #     conn.close()
# #     return True, [
# #         dbc.ModalHeader(f"Payment Results (Batch ID: {batch_id})"),
# #         dbc.ModalBody(dash_table.DataTable(
# #             data=df.to_dict('records'),
# #             columns=[{'name': i.replace('_', ' ').title(), 'id': i} for i in df.columns],
# #             style_table={'overflowX': 'auto'},
# #             editable=False,
# #             style_data_conditional=[
# #                 {'if': {'filter_query': '{status} = "paid"'}, 'backgroundColor': '#d4edda'},
# #                 {'if': {'filter_query': '{status} = "failed"'}, 'backgroundColor': '#f8d7da'}
# #             ]
# #         ))
# #     ]
# #
# #
# # @app.callback(
# #     Output("history-collapse", "is_open"),
# #     Input("toggle-history-btn", "n_clicks"),
# #     State("history-collapse", "is_open"),
# #     prevent_initial_call=True
# # )
# # def toggle_history_collapse(n, is_open):
# #     if n: return not is_open
# #     return is_open
# #
# #
# # @app.callback(
# #     Output("payment-history-placeholder", "children"),
# #     Input("history-collapse", "is_open"),
# #     Input("ipn-data-store", "data")
# # )
# # def render_payment_history(is_open, ipn_data):
# #     if not is_open: return None
# #     conn = sqlite3.connect('farmers_payment_module.db')
# #     df = pd.read_sql_query("SELECT * FROM payment_history ORDER BY processing_timestamp DESC", conn)
# #     conn.close()
# #     if df.empty: return dbc.Alert("No processed payments found.", color="secondary")
# #     df['processing_timestamp'] = pd.to_datetime(df['processing_timestamp']).dt.strftime('%Y-%m-%d %I:%M:%S %p')
# #
# #     cooperatives = sorted(df['cooperative_name'].unique())
# #     colors = ['#E6E6FA', '#FFF0F5', '#F0FFF0', '#F5FFFA', '#F0F8FF', '#F8F8FF', '#FFF5EE', '#FAFAD2']
# #     color_map = {coop: colors[i % len(colors)] for i, coop in enumerate(cooperatives)}
# #
# #     style_data_conditional = [
# #         {
# #             'if': {'filter_query': f'{{cooperative_name}} = "{coop_name}"'},
# #             'backgroundColor': color
# #         } for coop_name, color in color_map.items()
# #     ]
# #
# #     return dash_table.DataTable(
# #         data=df.to_dict('records'),
# #         columns=[{'name': i.replace('_', ' ').title(), 'id': i} for i in df.columns],
# #         page_size=10,
# #         style_table={'overflowX': 'auto'},
# #         editable=False,
# #         style_data_conditional=style_data_conditional
# #     )
# #
# #
# # @app.callback(
# #     Output("logs-collapse", "is_open"),
# #     Input("toggle-logs-btn", "n_clicks"),
# #     State("logs-collapse", "is_open"),
# #     prevent_initial_call=True
# # )
# # def toggle_logs_collapse(n, is_open):
# #     if n: return not is_open
# #     return is_open
# #
# #
# # @app.callback(
# #     Output("activity-logs-placeholder", "children"),
# #     Input("logs-collapse", "is_open"),
# #     Input("ipn-data-store", "data")
# # )
# # def render_activity_logs(is_open, ipn_data):
# #     if not is_open: return None
# #     conn = sqlite3.connect('farmers_payment_module.db')
# #     df = pd.read_sql_query(
# #         "SELECT timestamp, cooperative_name, action, details FROM activity_logs ORDER BY timestamp DESC", conn)
# #     conn.close()
# #     if df.empty: return dbc.Alert("No user activity found.", color="secondary")
# #     df['timestamp'] = pd.to_datetime(df['timestamp']).dt.strftime('%Y-%m-%d %I:%M:%S %p')
# #     return dash_table.DataTable(
# #         data=df.to_dict('records'),
# #         columns=[{'name': i.replace('_', ' ').title(), 'id': i} for i in df.columns],
# #         page_size=10, style_table={'overflowX': 'auto'}, editable=False,
# #         style_cell={'whiteSpace': 'normal', 'height': 'auto', 'textAlign': 'left'}
# #     )
# #
# #
# # @app.callback(
# #     Output("master-data-collapse", "is_open"),
# #     Input("toggle-master-data-btn", "n_clicks"),
# #     State("master-data-collapse", "is_open"),
# #     prevent_initial_call=True
# # )
# # def toggle_master_data_collapse(n, is_open):
# #     if n: return not is_open
# #     return is_open
# #
# #
# # @app.callback(
# #     Output("master-data-placeholder", "children"),
# #     Input("master-data-collapse", "is_open"),
# #     Input("ipn-data-store", "data")
# # )
# # def render_master_data_table(is_open, ipn_data):
# #     if not is_open:
# #         return None
# #
# #     conn = sqlite3.connect('farmers_payment_module.db')
# #     query = """
# #         SELECT
# #             b.submission_timestamp,
# #             u.cooperative_name,
# #             b.filename,
# #             p.farmer_name,
# #             p.bank_name,
# #             p.account_number,
# #             p.amount,
# #             p.status,
# #             p.failure_reason
# #         FROM
# #             farmer_payments AS p
# #         JOIN
# #             submission_batches AS b ON p.batch_id = b.id
# #         JOIN
# #             users AS u ON b.cooperative_id = u.id
# #         ORDER BY
# #             b.submission_timestamp DESC;
# #     """
# #     try:
# #         df = pd.read_sql_query(query, conn)
# #     finally:
# #         conn.close()
# #
# #     if df.empty:
# #         return dbc.Alert("No cooperative data has been submitted yet.", color="secondary")
# #
# #     df['submission_timestamp'] = pd.to_datetime(df['submission_timestamp']).dt.strftime('%Y-%m-%d %I:%M %p')
# #
# #     return dash_table.DataTable(
# #         data=df.to_dict('records'),
# #         columns=[{'name': col.replace('_', ' ').title(), 'id': col} for col in df.columns],
# #         page_size=15,
# #         style_table={'overflowX': 'auto'},
# #         style_cell={'textAlign': 'left', 'whiteSpace': 'normal', 'height': 'auto'},
# #         filter_action="native",
# #         sort_action="native",
# #         sort_by=[{'column_id': 'submission_timestamp', 'direction': 'desc'}]
# #     )
# #
# #
# # # --- Run Application ---
# # if __name__ == "__main__":
# #     init_db()
# #     app.run(debug=True, port=8057)
#
#
# import dash
# from dash import dcc, html, Input, Output, State, dash_table, callback_context, ALL
# import dash_bootstrap_components as dbc
# import pandas as pd
# import sqlite3
# import hashlib
# from datetime import datetime
# import base64
# import io
# import random
# import json
# import plotly.express as px
#
# # Initialize Dash app
# app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP], suppress_callback_exceptions=True)
# app.title = "Farmers Payment Module - Simplified Payment System"
#
#
# # --- Database Setup ---
# def init_db():
#     conn = sqlite3.connect('farmers_payment_module.db')
#     cursor = conn.cursor()
#
#     # Users table
#     cursor.execute('''
#         CREATE TABLE IF NOT EXISTS users (
#             id INTEGER PRIMARY KEY AUTOINCREMENT,
#             username TEXT UNIQUE NOT NULL,
#             password TEXT NOT NULL,
#             role TEXT NOT NULL,
#             cooperative_name TEXT
#         )
#     ''')
#
#     # Submission Batches table
#     cursor.execute('''
#         CREATE TABLE IF NOT EXISTS submission_batches (
#             id INTEGER PRIMARY KEY AUTOINCREMENT,
#             cooperative_id INTEGER,
#             filename TEXT,
#             record_count INTEGER,
#             total_amount REAL,
#             submission_timestamp TIMESTAMP,
#             status TEXT,
#             admin_notes TEXT,
#             cooperative_notes TEXT,
#             FOREIGN KEY (cooperative_id) REFERENCES users (id)
#         )
#     ''')
#
#     # Farmer Payments table
#     cursor.execute('''
#         CREATE TABLE IF NOT EXISTS farmer_payments (
#             id INTEGER PRIMARY KEY AUTOINCREMENT,
#             batch_id INTEGER,
#             farmer_name TEXT NOT NULL,
#             bank_name TEXT NOT NULL,
#             account_number TEXT NOT NULL,
#             amount REAL NOT NULL,
#             status TEXT DEFAULT 'pending',
#             failure_reason TEXT,
#             FOREIGN KEY (batch_id) REFERENCES submission_batches (id)
#         )
#     ''')
#
#     # Payment History table
#     cursor.execute('''
#         CREATE TABLE IF NOT EXISTS payment_history (
#             id INTEGER PRIMARY KEY AUTOINCREMENT,
#             batch_id INTEGER,
#             cooperative_name TEXT,
#             filename TEXT,
#             record_count INTEGER,
#             total_amount REAL,
#             processing_timestamp TIMESTAMP
#         )
#     ''')
#
#     # Activity Logs table
#     cursor.execute('''
#         CREATE TABLE IF NOT EXISTS activity_logs (
#             id INTEGER PRIMARY KEY AUTOINCREMENT,
#             timestamp TIMESTAMP,
#             user_id INTEGER,
#             cooperative_name TEXT,
#             action TEXT,
#             details TEXT,
#             FOREIGN KEY (user_id) REFERENCES users (id)
#         )
#     ''')
#
#     # Pre-populate with default users if table is empty
#     cursor.execute("SELECT COUNT(*) from users")
#     if cursor.fetchone()[0] == 0:
#         admin_password = hashlib.sha256("admin123".encode()).hexdigest()
#         coop_password = hashlib.sha256("coop123".encode()).hexdigest()
#         users_to_add = [
#             ("admin", admin_password, "admin", "Farmers Payment Module Admin"),
#             ("kcu", coop_password, "cooperative", "Kilimanjaro Cooperative Union"),
#             ("mbeyacof", coop_password, "cooperative", "Mbeya Coffee Union"),
#             ("dodoma_coop", coop_password, "cooperative", "Dodoma Grain Cooperative"),
#             ("tanga_coop", coop_password, "cooperative", "Tanga Sisal Cooperative"),
#             ("iringa_coop", coop_password, "cooperative", "Iringa Maize Cooperative"),
#             ("morogoro_coop", coop_password, "cooperative", "Morogoro Rice Cooperative"),
#             ("ruvuma_coop", coop_password, "cooperative", "Ruvuma Cashew Cooperative")
#         ]
#         for user in users_to_add:
#             cursor.execute(
#                 "INSERT OR IGNORE INTO users (username, password, role, cooperative_name) VALUES (?, ?, ?, ?)", user)
#
#     conn.commit()
#     conn.close()
#
#
# # --- Utility Functions ---
# def log_activity(user_id, action, details=""):
#     conn = sqlite3.connect('farmers_payment_module.db')
#     cursor = conn.cursor()
#     cursor.execute("SELECT cooperative_name FROM users WHERE id = ?", (user_id,))
#     cooperative_name = cursor.fetchone()[0]
#     cursor.execute(
#         "INSERT INTO activity_logs (timestamp, user_id, cooperative_name, action, details) VALUES (?, ?, ?, ?, ?)",
#         (datetime.now(), user_id, cooperative_name, action, details))
#     conn.commit()
#     conn.close()
#
#
# def authenticate_user(username, password):
#     conn = sqlite3.connect('farmers_payment_module.db')
#     cursor = conn.cursor()
#     cursor.execute("SELECT id, password, role, cooperative_name FROM users WHERE username = ?", (username,))
#     user = cursor.fetchone()
#     conn.close()
#     if user and user[1] == hashlib.sha256(password.encode()).hexdigest():
#         return {"id": user[0], "username": username, "role": user[2], "cooperative_name": user[3]}
#     return None
#
#
# # --- Layout Definitions ---
# def create_login_layout():
#     return dbc.Container([
#         dbc.Row(dbc.Col(dbc.Card([
#             dbc.CardBody([
#                 html.H2("Farmers Payment Module", className="text-center mb-4 text-success"),
#                 dbc.Input(id="login-username", placeholder="Username", type="text", className="mb-3"),
#                 dbc.Input(id="login-password", placeholder="Password", type="password", className="mb-3"),
#                 dbc.Button("Login", id="login-button", color="success", className="w-100"),
#                 html.Div(id="login-alert-placeholder", className="mt-3")
#             ])
#         ], className="shadow"), width=10, sm=8, md=6, lg=4), justify="center",
#             className="min-vh-100 align-items-center"),
#
#         dbc.Alert([
#             html.H5("Demo Credentials", className="alert-heading"),
#             html.P([html.B("Admin Account:")]),
#             html.Ul([
#                 html.Li(["Username: ", html.Code("admin"), " | Password: ", html.Code("admin123")])
#             ]),
#             html.P([html.B("Cooperative Accounts:")]),
#             html.Ul([
#                 html.Li(["Username: ", html.Code("kcu"), " | Password: ", html.Code("coop123")]),
#                 html.Li(["Username: ", html.Code("mbeyacof"), " | Password: ", html.Code("coop123")]),
#                 html.Li(["Username: ", html.Code("dodoma_coop"), " | Password: ", html.Code("coop123")]),
#                 html.Li(["Username: ", html.Code("tanga_coop"), " | Password: ", html.Code("coop123")]),
#                 html.Li(["Username: ", html.Code("iringa_coop"), " | Password: ", html.Code("coop123")]),
#             ])
#         ], color="info", style={"position": "absolute", "bottom": "10px", "left": "10px", "width": "auto"})
#     ], fluid=True, className="bg-light")
#
#
# def create_cooperative_layout(session_data):
#     return html.Div([
#         dbc.NavbarSimple(brand=session_data.get('cooperative_name'),
#                          children=[dbc.Button("Logout", id="logout-button", color="light", outline=True)],
#                          color="success", dark=True),
#         dbc.Container([
#             dbc.Alert(id="coop-alert", is_open=False, duration=4000),
#             html.H3("Farmer Data Submission  Portal", className="my-4"),
#             dcc.Upload(id='upload-data', children=html.Div(['Drag and Drop or ', html.A('Select a CSV/Excel File')]),
#                        style={'width': '100%', 'height': '60px', 'lineHeight': '60px', 'borderWidth': '1px',
#                               'borderStyle': 'dashed', 'borderRadius': '5px', 'textAlign': 'center',
#                               'margin': '10px 0'},
#                        multiple=False),
#             html.Hr(),
#             html.Div(id="submission-table-placeholder"),
#             html.Hr(),
#             html.H3("Submission History", className="my-4"),
#             html.Div(id="coop-history-placeholder"),
#         ], fluid=True),
#         dbc.Modal(id="coop-results-modal", size="xl", is_open=False)
#     ])
#
#
# # --- THIS FUNCTION HAS BEEN UPDATED ---
# def create_admin_layout(session_data):
#     return html.Div([
#         dbc.Toast(id="ipn-toast", is_open=False, duration=6000, icon="success",
#                   style={"position": "fixed", "top": 20, "right": 20, "width": 350, "zIndex": 9999}),
#         dbc.NavbarSimple(brand="Admin Payments Dashboard",
#                          children=[dbc.Button("Logout", id="logout-button", color="light", outline=True)],
#                          color="primary", dark=True),
#         dbc.Container([
#             html.Div(id="kpi-cards-placeholder"),
#             html.Div(id="admin-dashboard-content"),
#             html.Hr(),
#
#             # Replaced separate sections with a Tabbed interface
#             dbc.Tabs(id="admin-tabs", active_tab="tab-analytics", children=[
#                 dbc.Tab(label="📊 Analytics", tab_id="tab-analytics", children=[
#                     html.Div(id="analytics-tab-content", className="py-4")
#                 ]),
#                 dbc.Tab(label="📄 Master Payment Data", tab_id="tab-master-data", children=[
#                     html.Div(className="py-4", children=[
#                         dbc.Collapse(html.Div(id="master-data-placeholder"), id="master-data-collapse", is_open=True)
#                     ])
#                 ]),
#                 dbc.Tab(label="📜 Payment History", tab_id="tab-history", children=[
#                     html.Div(className="py-4", children=[
#                         dbc.Collapse(html.Div(id="payment-history-placeholder"), id="history-collapse", is_open=True)
#                     ])
#                 ]),
#                 dbc.Tab(label="📝 User Activity Logs", tab_id="tab-logs", children=[
#                     html.Div(className="py-4", children=[
#                         dbc.Collapse(html.Div(id="activity-logs-placeholder"), id="logs-collapse", is_open=True)
#                     ])
#                 ]),
#             ]),
#         ], fluid=True, className="py-4"),
#         dbc.Modal(id="details-modal", size="xl", is_open=False),
#         dbc.Modal([
#             dbc.ModalHeader("Processing Payment"),
#             dbc.ModalBody(id="payment-animation-placeholder"),
#             dbc.ModalFooter(dbc.Button("Close", id="payment-close-button", color="secondary", disabled=True))
#         ], id="payment-modal", backdrop="static")
#     ])
#
#
# # Main App Layout
# app.layout = html.Div([
#     dcc.Store(id="user-session", storage_type="session"),
#     dcc.Store(id="batch-to-process"),
#     dcc.Store(id='ipn-data-store'),
#     dcc.Interval(id='payment-interval', interval=1500, n_intervals=0, disabled=True),
#     dcc.Store(id='submission-trigger-store'),
#     html.Div(id="main-content")
# ])
#
#
# # --- Callbacks ---
#
# # --- THIS CALLBACK HAS BEEN UPDATED ---
# @app.callback(
#     Output("kpi-cards-placeholder", "children"),
#     Input("user-session", "data"),
#     Input("ipn-data-store", "data"),
#     Input("submission-trigger-store", "data")
# )
# def update_kpi_cards(session_data, ipn_data, submission_trigger):
#     if not session_data or session_data.get("role") != "admin":
#         return None
#
#     conn = sqlite3.connect('farmers_payment_module.db')
#     cursor = conn.cursor()
#
#     # TMX Funds Card - Now shows a static "received" amount
#     tmx_amount_received = 500000000  # Static value representing funds received
#
#     # KPI 1: Total Amount Paid
#     cursor.execute("SELECT SUM(amount) FROM farmer_payments WHERE status = 'paid'")
#     total_paid = cursor.fetchone()[0] or 0
#
#     # KPI 2: Total Farmers Paid
#     cursor.execute("SELECT COUNT(id) FROM farmer_payments WHERE status = 'paid'")
#     farmers_paid_count = cursor.fetchone()[0] or 0
#
#     # KPI 3: Pending Payments
#     cursor.execute("SELECT COUNT(id) FROM submission_batches WHERE status = 'pending_approval'")
#     pending_submissions = cursor.fetchone()[0] or 0
#
#     # KPI 4: Number of Cooperatives
#     cursor.execute("SELECT COUNT(id) FROM users WHERE role = 'cooperative'")
#     coop_count = cursor.fetchone()[0] or 0
#
#     conn.close()
#
#     tmx_card = dbc.Card(
#         dbc.CardBody([
#             html.P("Funds Received from TMX", className="card-text text-muted small"),
#             html.H3(f"TSH {tmx_amount_received:,.2f}", className="card-title text-success"),
#             html.P(f"Latest deposit received on {datetime.now().strftime('%Y-%m-%d')}", className="card-text"),
#         ]),
#         className="mb-4",
#         style={"border-left": "5px solid #198754"}
#     )
#
#     kpi_cards = dbc.Row([
#         dbc.Col(dbc.Card(dbc.CardBody([
#             html.H4(f"TSH {total_paid:,.2f}", className="card-title"),
#             html.P("Total Amount Paid", className="card-text text-muted"),
#         ])), width=6, lg=3, className="mb-3"),
#         dbc.Col(dbc.Card(dbc.CardBody([
#             html.H4(f"{farmers_paid_count:,}", className="card-title"),
#             html.P("Total Farmers Paid", className="card-text text-muted"),
#         ])), width=6, lg=3, className="mb-3"),
#         dbc.Col(dbc.Card(dbc.CardBody([
#             html.H4(pending_submissions, className="card-title text-warning"),
#             html.P("Pending Payments", className="card-text text-muted"),
#         ])), width=6, lg=3, className="mb-3"),
#         dbc.Col(dbc.Card(dbc.CardBody([
#             html.H4(coop_count, className="card-title"),
#             html.P("Active Cooperatives", className="card-text text-muted"),
#         ])), width=6, lg=3, className="mb-3"),
#     ])
#
#     return html.Div([tmx_card, kpi_cards])
#
#
# @app.callback(
#     Output("main-content", "children"),
#     Input("user-session", "data")
# )
# def display_page(session_data):
#     if session_data:
#         if session_data.get("role") == "admin":
#             return create_admin_layout(session_data)
#         elif session_data.get("role") == "cooperative":
#             return create_cooperative_layout(session_data)
#     return create_login_layout()
#
#
# @app.callback(
#     Output("user-session", "data"),
#     Output("login-alert-placeholder", "children"),
#     Input("login-button", "n_clicks"),
#     State("login-username", "value"),
#     State("login-password", "value"),
#     prevent_initial_call=True
# )
# def handle_login(n_clicks, username, password):
#     if not username or not password: return dash.no_update, dbc.Alert("Fields cannot be empty.", color="warning")
#     user = authenticate_user(username, password)
#     if user:
#         log_activity(user['id'], 'Login', f"User '{user['username']}' logged in.")
#         return user, None
#     return None, dbc.Alert("Invalid credentials.", color="danger")
#
#
# @app.callback(
#     Output("user-session", "data", allow_duplicate=True),
#     Input("logout-button", "n_clicks"),
#     prevent_initial_call=True
# )
# def handle_logout(n_clicks):
#     if n_clicks: return None
#     return dash.no_update
#
#
# @app.callback(
#     Output("submission-table-placeholder", "children"),
#     Input('upload-data', 'contents'),
#     State('upload-data', 'filename'),
#     prevent_initial_call=True
# )
# def update_output(contents, filename):
#     if contents is None: return html.Div()
#     content_type, content_string = contents.split(',')
#     decoded = base64.b64decode(content_string)
#     try:
#         df = pd.read_csv(io.StringIO(decoded.decode('utf-8'))) if 'csv' in filename else pd.read_excel(
#             io.BytesIO(decoded))
#         required_cols = {'farmer_name', 'bank_name', 'account_number', 'amount'}
#         if not required_cols.issubset(df.columns): return dbc.Alert(
#             f"File is missing columns: {required_cols - set(df.columns)}", color="danger")
#         return html.Div([
#             dcc.Store(id='submission-data', data={'df': df.to_dict('records'), 'filename': filename}),
#             html.H5("Review Data"),
#             dash_table.DataTable(id='editable-datatable', data=df.to_dict('records'),
#                                  columns=[{'name': i, 'id': i} for i in df.columns], page_size=10,
#                                  style_table={'overflowX': 'auto'}, editable=True),
#             html.Hr(),
#             dbc.Label("Note to Admin (Optional)", html_for="coop-note-textarea"),
#             dbc.Textarea(id='coop-note-textarea', placeholder="Add notes for the admin regarding this submission...",
#                          className="mb-3"),
#             html.Div(dbc.Button("Submit to Admin", id="submit-to-admin-button", color="primary"),
#                      className="d-flex justify-content-end")
#         ])
#     except Exception as e:
#         return dbc.Alert(f"Error processing file: {e}", color="danger")
#
#
# @app.callback(
#     Output("coop-alert", "children"),
#     Output("coop-alert", "is_open"),
#     Output("coop-alert", "color"),
#     Output("submission-table-placeholder", "children", allow_duplicate=True),
#     Output("submission-trigger-store", "data"),
#     Input("submit-to-admin-button", "n_clicks"),
#     State("editable-datatable", "data"),
#     State("submission-data", "data"),
#     State("user-session", "data"),
#     State("coop-note-textarea", "value"),
#     prevent_initial_call=True
# )
# def submit_to_admin(n_clicks, table_data, submission_data_store, session_data, coop_note):
#     if not n_clicks or not table_data: return "", False, "", dash.no_update, dash.no_update
#     df = pd.DataFrame(table_data)
#     filename = submission_data_store.get('filename', 'uploaded_file')
#     conn = sqlite3.connect('farmers_payment_module.db')
#     cursor = conn.cursor()
#     try:
#         cursor.execute(
#             "INSERT INTO submission_batches (cooperative_id, filename, record_count, total_amount, submission_timestamp, status, cooperative_notes) VALUES (?, ?, ?, ?, ?, ?, ?)",
#             (session_data['id'], filename, len(df), df['amount'].sum(), datetime.now(), 'pending_approval', coop_note))
#         batch_id = cursor.lastrowid
#         df_to_db = df[['farmer_name', 'bank_name', 'account_number', 'amount']]
#         df_to_db['batch_id'] = batch_id
#         df_to_db.to_sql('farmer_payments', conn, if_exists='append', index=False)
#         conn.commit()
#         log_activity(session_data['id'], 'Data Submission', f"Submitted '{filename}' with {len(df)} records.")
#         msg, color = f"Successfully submitted {len(df)} records.", "success"
#         return msg, True, color, html.Div(), datetime.now().isoformat()
#     except Exception as e:
#         conn.rollback()
#         msg, color = f"Database error: {e}", "danger"
#     finally:
#         conn.close()
#     return msg, True, color, dash.no_update, dash.no_update
#
#
# @app.callback(
#     Output("admin-dashboard-content", "children"),
#     Input("user-session", "data"),
#     Input("ipn-data-store", "data"),
#     Input("submission-trigger-store", "data")
# )
# def render_admin_dashboard(session_data, ipn_data, submission_trigger):
#     if not session_data or session_data.get("role") != "admin": return None
#     conn = sqlite3.connect('farmers_payment_module.db')
#     query = "SELECT b.id, u.cooperative_name, b.filename, b.record_count, b.total_amount FROM submission_batches b JOIN users u ON b.cooperative_id = u.id WHERE b.status = 'pending_approval' ORDER BY b.submission_timestamp DESC"
#     batches_df = pd.read_sql_query(query, conn)
#     conn.close()
#     if batches_df.empty: return dbc.Alert("No Pending Payments found.", color="info", className="m-4")
#     cards = [dbc.Card([
#         dbc.CardHeader(f"From: {row['cooperative_name']}"),
#         dbc.CardBody([
#             html.H5(row['filename'], className="card-title"),
#             html.P(f"{row['record_count']} farmers, Total: TSH {row['total_amount']:,.2f}")
#         ]),
#         dbc.CardFooter(html.Div([
#             dbc.Button("View Details", id={'type': 'view-details-btn', 'index': row['id']}, color="secondary"),
#             dbc.Button("Pay Now", id={'type': 'pay-now-btn', 'index': row['id']}, color="success"),
#         ], className="d-flex justify-content-between"))
#     ], className="mb-3") for _, row in batches_df.iterrows()]
#     return [html.H3("Pending Payments", className="mb-4")] + cards
#
#
# @app.callback(
#     Output("details-modal", "is_open"),
#     Output("details-modal", "children"),
#     Input({'type': 'view-details-btn', 'index': ALL}, 'n_clicks'),
#     prevent_initial_call=True
# )
# def toggle_details_modal(n_clicks):
#     if not any(n_clicks): return False, None
#     batch_id = int(eval(callback_context.triggered[0]['prop_id'].split('.')[0])['index'])
#     conn = sqlite3.connect('farmers_payment_module.db')
#     df = pd.read_sql_query(
#         "SELECT farmer_name, bank_name, account_number, amount FROM farmer_payments WHERE batch_id = ?", conn,
#         params=(batch_id,))
#     notes_df = pd.read_sql_query("SELECT admin_notes, cooperative_notes FROM submission_batches WHERE id = ?", conn,
#                                  params=(batch_id,))
#     conn.close()
#     admin_note, coop_note = notes_df['admin_notes'].iloc[0] or "", notes_df['cooperative_notes'].iloc[0]
#     return True, [
#         dbc.ModalHeader(f"Submission Details (Batch ID: {batch_id})"),
#         dbc.ModalBody([
#             dash_table.DataTable(data=df.to_dict('records'), columns=[{'name': i, 'id': i} for i in df.columns],
#                                  style_table={'maxHeight': '40vh', 'overflowY': 'auto'}),
#             html.Hr(),
#             html.H5("Communication"),
#             dbc.Label("Note from Cooperative:"),
#             dbc.Alert(coop_note, color="info") if coop_note else html.P("No note provided.",
#                                                                         className="text-muted fst-italic"),
#             dbc.Label("Your Response to Cooperative:", className="mt-2"),
#             dbc.Alert(id="note-save-alert", is_open=False, duration=3000),
#             dcc.Textarea(id={'type': 'admin-note-textarea', 'index': batch_id}, value=admin_note,
#                          style={'width': '100%', 'height': 100}),
#             dbc.Button("Save Response", id={'type': 'save-note-btn', 'index': batch_id}, color="primary",
#                        className="mt-2")
#         ])
#     ]
#
#
# @app.callback(
#     Output("note-save-alert", "is_open"),
#     Output("note-save-alert", "children"),
#     Output("note-save-alert", "color"),
#     Input({'type': 'save-note-btn', 'index': ALL}, 'n_clicks'),
#     State({'type': 'admin-note-textarea', 'index': ALL}, 'value'),
#     prevent_initial_call=True
# )
# def save_admin_note(n_clicks, notes):
#     if not any(n_clicks): return False, "", ""
#     ctx = callback_context.triggered[0]
#     batch_id = int(eval(ctx['prop_id'].split('.')[0])['index'])
#     note_value = notes[0]
#     try:
#         conn = sqlite3.connect('farmers_payment_module.db')
#         cursor = conn.cursor()
#         cursor.execute("UPDATE submission_batches SET admin_notes = ? WHERE id = ?", (note_value, batch_id))
#         conn.commit()
#         conn.close()
#         return True, "Response saved successfully!", "success"
#     except Exception as e:
#         return True, f"Error saving response: {e}", "danger"
#
#
# @app.callback(
#     Output("payment-modal", "is_open"),
#     Output("payment-interval", "disabled"),
#     Output("payment-animation-placeholder", "children"),
#     Output("payment-close-button", "disabled"),
#     Output("batch-to-process", "data"),
#     Output("ipn-data-store", "data"),
#     Input({'type': 'pay-now-btn', 'index': ALL}, 'n_clicks'),
#     Input("payment-interval", "n_intervals"),
#     Input("payment-close-button", "n_clicks"),
#     State("batch-to-process", "data"),
#     State("user-session", "data"),
#     prevent_initial_call=True
# )
# def handle_payment_processing(pay_clicks, n_intervals, close_clicks, batch_id, session_data):
#     ctx = callback_context
#     if not ctx.triggered:
#         return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update
#
#     triggered_id_str = ctx.triggered[0]['prop_id']
#     triggered_value = ctx.triggered[0]['value']
#
#     if 'pay-now-btn' in triggered_id_str and triggered_value is not None:
#         id_dict = json.loads(triggered_id_str.split('.')[0])
#         new_batch_id = id_dict['index']
#
#         animation_step = html.Div([
#             html.Div("🔄", style={'fontSize': 50}),
#             dbc.Progress(value=5),
#             html.P("Initiating...")
#         ], className="text-center")
#         return True, False, animation_step, True, new_batch_id, dash.no_update
#
#     elif 'payment-interval' in triggered_id_str and batch_id is not None:
#         if n_intervals < 4:
#             progress = (n_intervals + 1) * 25
#             animation_step = html.Div([
#                 html.Div("🔄", style={'fontSize': 50}),
#                 dbc.Progress(value=progress, striped=True, animated=True),
#                 html.P("Processing...")
#             ], className="text-center")
#             return True, False, animation_step, True, batch_id, dash.no_update
#         else:
#             conn = sqlite3.connect('farmers_payment_module.db')
#             cursor = conn.cursor()
#             cursor.execute(
#                 "SELECT u.cooperative_name, b.filename, b.record_count, b.total_amount FROM submission_batches b JOIN users u ON b.cooperative_id = u.id WHERE b.id = ?",
#                 (batch_id,))
#             batch_info = cursor.fetchone()
#             cursor.execute("UPDATE submission_batches SET status = 'processed' WHERE id = ?", (batch_id,))
#
#             payments, success, failed = [], 0, 0
#             reasons = ["Invalid Account", "Bank Error", "Name Mismatch"]
#             cursor.execute("SELECT id FROM farmer_payments WHERE batch_id = ?", (batch_id,))
#             for (pid,) in cursor.fetchall():
#                 if random.random() < 0.95:
#                     success += 1;
#                     payments.append(('paid', None, pid))
#                 else:
#                     failed += 1;
#                     payments.append(('failed', random.choice(reasons), pid))
#             cursor.executemany("UPDATE farmer_payments SET status = ?, failure_reason = ? WHERE id = ?", payments)
#
#             if batch_info:
#                 coop_name, filename, record_count, total_amount = batch_info
#                 cursor.execute(
#                     "INSERT INTO payment_history (batch_id, cooperative_name, filename, record_count, total_amount, processing_timestamp) VALUES (?, ?, ?, ?, ?, ?)",
#                     (batch_id, coop_name, filename, record_count, total_amount, datetime.now()))
#             conn.commit()
#             conn.close()
#
#             log_activity(session_data['id'], 'Payment Processed',
#                          f"Processed '{batch_info[1]}' for {batch_info[0]}. Success: {success}, Failed: {failed}.")
#             ipn = {'coop': batch_info[0], 'success': success, 'failed': failed, 'total': batch_info[2]}
#             result = html.Div([
#                 html.Div("✅", style={'fontSize': 60, 'color': 'green'}),
#                 dbc.Progress(value=100, color="success"),
#                 html.H5("Payment Processed!")
#             ], className="text-center")
#             return True, True, result, False, None, ipn
#
#     elif 'payment-close-button' in triggered_id_str:
#         return False, True, "", True, None, dash.no_update
#
#     return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update
#
#
# @app.callback(
#     Output("ipn-toast", "is_open"),
#     Output("ipn-toast", "header"),
#     Output("ipn-toast", "children"),
#     Output("ipn-toast", "icon"),
#     Input("ipn-data-store", "data"),
#     prevent_initial_call=True
# )
# def show_ipn_toast(data):
#     if not data: return False, "", "", ""
#     header, icon = "IPN: Transaction Complete", "warning" if data['failed'] > 0 else "success"
#     body = f"{data['coop']}: Paid {data['success']}/{data['total']} farmers. ({data['failed']} failed)"
#     return True, header, body, icon
#
#
# @app.callback(
#     Output("coop-history-placeholder", "children"),
#     Input("user-session", "data"),
#     Input("coop-alert", "is_open")
# )
# def render_coop_history(session_data, alert_is_open):
#     if not session_data or session_data.get("role") != "cooperative": return None
#     conn = sqlite3.connect('farmers_payment_module.db')
#     df = pd.read_sql_query(
#         "SELECT id, filename, status, admin_notes, submission_timestamp FROM submission_batches WHERE cooperative_id = ? ORDER BY submission_timestamp DESC",
#         conn, params=(session_data['id'],))
#     conn.close()
#     if df.empty: return dbc.Alert("No submissions yet.", color="info")
#     return dbc.Accordion([
#         dbc.AccordionItem([
#             html.P(
#                 f"Submitted on: {datetime.strptime(row['submission_timestamp'].split('.')[0], '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d %I:%M %p')}"),
#             dbc.Alert(f"Admin Response: {row['admin_notes']}", color="info") if row['admin_notes'] else "",
#             dbc.Button("View Results", id={'type': 'view-results-btn', 'index': row['id']}) if row[
#                                                                                                    'status'] == 'processed' else ""
#         ], title=html.Div([
#             row['filename'],
#             dbc.Badge(row['status'].replace('_', ' ').title(), className="ms-2",
#                       color="success" if row['status'] == 'processed' else "warning")
#         ]))
#         for _, row in df.iterrows()
#     ], start_collapsed=True)
#
#
# @app.callback(
#     Output('coop-results-modal', 'is_open'),
#     Output('coop-results-modal', 'children'),
#     Input({'type': 'view-results-btn', 'index': ALL}, 'n_clicks'),
#     prevent_initial_call=True
# )
# def show_coop_results_modal(n_clicks):
#     if not any(n_clicks): return False, None
#     batch_id = int(eval(callback_context.triggered[0]['prop_id'].split('.')[0])['index'])
#     conn = sqlite3.connect('farmers_payment_module.db')
#     df = pd.read_sql_query(
#         "SELECT farmer_name, bank_name, account_number, amount, status, failure_reason FROM farmer_payments WHERE batch_id = ?",
#         conn, params=(batch_id,))
#     conn.close()
#     return True, [
#         dbc.ModalHeader(f"Payment Results (Batch ID: {batch_id})"),
#         dbc.ModalBody(dash_table.DataTable(
#             data=df.to_dict('records'),
#             columns=[{'name': i.replace('_', ' ').title(), 'id': i} for i in df.columns],
#             style_table={'overflowX': 'auto'},
#             editable=False,
#             style_data_conditional=[
#                 {'if': {'filter_query': '{status} = "paid"'}, 'backgroundColor': '#d4edda'},
#                 {'if': {'filter_query': '{status} = "failed"'}, 'backgroundColor': '#f8d7da'}
#             ]
#         ))
#     ]
#
#
# # This callback is now only responsible for the content of the History tab
# @app.callback(
#     Output("payment-history-placeholder", "children"),
#     Input("admin-tabs", "active_tab"),
#     Input("ipn-data-store", "data")
# )
# def render_payment_history(active_tab, ipn_data):
#     if active_tab != "tab-history":
#         return None
#     conn = sqlite3.connect('farmers_payment_module.db')
#     df = pd.read_sql_query("SELECT * FROM payment_history ORDER BY processing_timestamp DESC", conn)
#     conn.close()
#     if df.empty: return dbc.Alert("No processed payments found.", color="secondary")
#     df['processing_timestamp'] = pd.to_datetime(df['processing_timestamp']).dt.strftime('%Y-%m-%d %I:%M:%S %p')
#
#     cooperatives = sorted(df['cooperative_name'].unique())
#     colors = ['#E6E6FA', '#FFF0F5', '#F0FFF0', '#F5FFFA', '#F0F8FF', '#F8F8FF', '#FFF5EE', '#FAFAD2']
#     color_map = {coop: colors[i % len(colors)] for i, coop in enumerate(cooperatives)}
#
#     style_data_conditional = [
#         {
#             'if': {'filter_query': f'{{cooperative_name}} = "{coop_name}"'},
#             'backgroundColor': color
#         } for coop_name, color in color_map.items()
#     ]
#
#     return dash_table.DataTable(
#         data=df.to_dict('records'),
#         columns=[{'name': i.replace('_', ' ').title(), 'id': i} for i in df.columns],
#         page_size=10,
#         style_table={'overflowX': 'auto'},
#         editable=False,
#         style_data_conditional=style_data_conditional
#     )
#
#
# # This callback is now only responsible for the content of the Logs tab
# @app.callback(
#     Output("activity-logs-placeholder", "children"),
#     Input("admin-tabs", "active_tab"),
#     Input("ipn-data-store", "data")
# )
# def render_activity_logs(active_tab, ipn_data):
#     if active_tab != "tab-logs":
#         return None
#     conn = sqlite3.connect('farmers_payment_module.db')
#     df = pd.read_sql_query(
#         "SELECT timestamp, cooperative_name, action, details FROM activity_logs ORDER BY timestamp DESC", conn)
#     conn.close()
#     if df.empty: return dbc.Alert("No user activity found.", color="secondary")
#     df['timestamp'] = pd.to_datetime(df['timestamp']).dt.strftime('%Y-%m-%d %I:%M:%S %p')
#     return dash_table.DataTable(
#         data=df.to_dict('records'),
#         columns=[{'name': i.replace('_', ' ').title(), 'id': i} for i in df.columns],
#         page_size=10, style_table={'overflowX': 'auto'}, editable=False,
#         style_cell={'whiteSpace': 'normal', 'height': 'auto', 'textAlign': 'left'}
#     )
#
#
# # This callback is now only responsible for the content of the Master Data tab
# @app.callback(
#     Output("master-data-placeholder", "children"),
#     Input("admin-tabs", "active_tab"),
#     Input("ipn-data-store", "data")
# )
# def render_master_data_table(active_tab, ipn_data):
#     if active_tab != "tab-master-data":
#         return None
#
#     conn = sqlite3.connect('farmers_payment_module.db')
#     query = """
#         SELECT u.cooperative_name, b.submission_timestamp, b.filename, p.*
#         FROM farmer_payments AS p
#         JOIN submission_batches AS b ON p.batch_id = b.id
#         JOIN users AS u ON b.cooperative_id = u.id
#         ORDER BY b.submission_timestamp DESC;
#     """
#     try:
#         df = pd.read_sql_query(query, conn)
#     finally:
#         conn.close()
#
#     if df.empty:
#         return dbc.Alert("No cooperative data has been submitted yet.", color="secondary")
#
#     df['submission_timestamp'] = pd.to_datetime(df['submission_timestamp']).dt.strftime('%Y-%m-%d %I:%M %p')
#
#     cooperatives = sorted(df['cooperative_name'].unique())
#     colors = ['#E6E6FA', '#FFF0F5', '#F0FFF0', '#F5FFFA', '#F0F8FF', '#F8F8FF', '#FFF5EE', '#FAFAD2']
#     color_map = {coop: colors[i % len(colors)] for i, coop in enumerate(cooperatives)}
#
#     style_data_conditional = [
#         {
#             'if': {'filter_query': f'{{cooperative_name}} = "{coop_name}"'},
#             'backgroundColor': color
#         } for coop_name, color in color_map.items()
#     ]
#
#     return dash_table.DataTable(
#         data=df.to_dict('records'),
#         columns=[{'name': col.replace('_', ' ').title(), 'id': col} for col in df.columns],
#         page_size=15,
#         style_table={'overflowX': 'auto'},
#         style_cell={'textAlign': 'left', 'whiteSpace': 'normal', 'height': 'auto'},
#         filter_action="native",
#         sort_action="native",
#         sort_by=[{'column_id': 'submission_timestamp', 'direction': 'desc'}],
#         style_data_conditional=style_data_conditional
#     )
#
#
# # --- NEW CALLBACK FOR ANALYTICS TAB ---
# @app.callback(
#     Output("analytics-tab-content", "children"),
#     Input("admin-tabs", "active_tab"),
#     Input("ipn-data-store", "data")
# )
# def render_analytics_tab(active_tab, ipn_data):
#     if active_tab != "tab-analytics":
#         return None
#
#     conn = sqlite3.connect('farmers_payment_module.db')
#     query = """
#         SELECT b.submission_timestamp, u.cooperative_name, p.farmer_name, p.bank_name, p.amount, p.status
#         FROM farmer_payments AS p
#         JOIN submission_batches AS b ON p.batch_id = b.id
#         JOIN users AS u ON b.cooperative_id = u.id;
#     """
#     try:
#         df = pd.read_sql_query(query, conn)
#     finally:
#         conn.close()
#
#     if df.empty:
#         return dbc.Alert("No data available to generate analytics.", color="info")
#
#     df['date'] = pd.to_datetime(df['submission_timestamp']).dt.date
#     df_paid = df[df['status'] == 'paid']
#
#     # --- Calculations ---
#     bank_activity = df_paid.groupby('bank_name').agg(
#         total_amount=('amount', 'sum'),
#         account_holders=('farmer_name', 'nunique')
#     ).reset_index().sort_values('total_amount', ascending=False)
#
#     coop_activity = df_paid.groupby('cooperative_name').agg(
#         total_amount=('amount', 'sum'),
#         members=('farmer_name', 'nunique')
#     ).reset_index()
#
#     farmer_activity = df_paid.groupby('farmer_name').agg(
#         total_amount=('amount', 'sum'),
#         transaction_count=('farmer_name', 'count')
#     ).reset_index()
#
#     top_farmers_value = farmer_activity.sort_values('total_amount', ascending=False).head(10)
#     top_farmers_busy = farmer_activity.sort_values('transaction_count', ascending=False).head(10)
#
#     daily_trends = df_paid.groupby('date').agg(
#         total_amount=('amount', 'sum'),
#         unique_banks=('bank_name', 'nunique')
#     ).reset_index()
#
#     status_distribution = df.groupby(['date', 'status'])['status'].count().unstack(fill_value=0).reset_index()
#     status_distribution = pd.melt(status_distribution, id_vars=['date'], value_vars=['paid', 'failed'])
#
#     # --- Figures ---
#     fig_bank_amount = px.bar(bank_activity.head(10), x='bank_name', y='total_amount',
#                              title='Top 10 Banks by Transaction Value',
#                              labels={'bank_name': 'Bank', 'total_amount': 'Total Amount (TSH)'})
#     fig_bank_holders = px.bar(bank_activity.sort_values('account_holders', ascending=False).head(10), x='bank_name',
#                               y='account_holders', title='Top 10 Banks by Unique Farmers',
#                               labels={'bank_name': 'Bank', 'account_holders': 'Number of Farmers'})
#     fig_coop_value = px.pie(coop_activity, names='cooperative_name', values='total_amount',
#                             title='Transaction Value by Cooperative')
#     fig_coop_members = px.pie(coop_activity, names='cooperative_name', values='members',
#                               title='Unique Farmers by Cooperative')
#     fig_daily_trend = px.line(daily_trends, x='date', y='total_amount', title='Daily Transaction Volume (Amount)',
#                               markers=True)
#     fig_status_dist = px.bar(status_distribution, x='date', y='value', color='status',
#                              title='Paid vs. Failed Transactions Over Time', barmode='stack',
#                              color_discrete_map={'paid': 'green', 'failed': 'red'})
#
#     return html.Div([
#         dbc.Row([
#             dbc.Col(dcc.Graph(figure=fig_daily_trend), width=12),
#         ]),
#         html.Hr(),
#         dbc.Row([
#             dbc.Col(dcc.Graph(figure=fig_status_dist), width=12),
#         ]),
#         html.Hr(),
#         dbc.Row([
#             dbc.Col(dcc.Graph(figure=fig_bank_amount), md=6),
#             dbc.Col(dcc.Graph(figure=fig_bank_holders), md=6),
#         ]),
#         html.Hr(),
#         dbc.Row([
#             dbc.Col(dcc.Graph(figure=fig_coop_value), md=6),
#             dbc.Col(dcc.Graph(figure=fig_coop_members), md=6),
#         ]),
#         html.Hr(),
#         dbc.Row([
#             dbc.Col([
#                 html.H5("Top 10 Most Valuable Farmers"),
#                 dash_table.DataTable(data=top_farmers_value.to_dict('records'),
#                                      columns=[{'name': i.replace('_', ' ').title(), 'id': i} for i in
#                                               top_farmers_value.columns], style_table={'overflowX': 'auto'})
#             ], md=6),
#             dbc.Col([
#                 html.H5("Top 10 Busiest Farmers (by # of payments)"),
#                 dash_table.DataTable(data=top_farmers_busy.to_dict('records'),
#                                      columns=[{'name': i.replace('_', ' ').title(), 'id': i} for i in
#                                               top_farmers_busy.columns], style_table={'overflowX': 'auto'})
#             ], md=6),
#         ]),
#     ])
#
#
# # --- Run Application ---
# if __name__ == "__main__":
#     init_db()
#     app.run(debug=True, port=8035)


import dash
from dash import dcc, html, Input, Output, State, dash_table, callback_context, ALL
import dash_bootstrap_components as dbc
import pandas as pd
import sqlite3
import hashlib
from datetime import datetime
import base64
import io
import random
import json
import plotly.express as px

# Initialize Dash app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP], suppress_callback_exceptions=True)
app.title = "Farmers Payment Module - Simplified Payment System"


# --- Database Setup ---
def init_db():
    conn = sqlite3.connect('farmers_payment_module.db')
    cursor = conn.cursor()

    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL,
            cooperative_name TEXT
        )
    ''')

    # Submission Batches table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS submission_batches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cooperative_id INTEGER,
            filename TEXT,
            record_count INTEGER,
            total_amount REAL,
            submission_timestamp TIMESTAMP,
            status TEXT,
            admin_notes TEXT,
            cooperative_notes TEXT,
            FOREIGN KEY (cooperative_id) REFERENCES users (id)
        )
    ''')

    # Farmer Payments table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS farmer_payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            batch_id INTEGER,
            farmer_name TEXT NOT NULL,
            bank_name TEXT NOT NULL,
            account_number TEXT NOT NULL,
            amount REAL NOT NULL,
            status TEXT DEFAULT 'pending',
            failure_reason TEXT,
            FOREIGN KEY (batch_id) REFERENCES submission_batches (id)
        )
    ''')

    # Payment History table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS payment_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            batch_id INTEGER,
            cooperative_name TEXT,
            filename TEXT,
            record_count INTEGER,
            total_amount REAL,
            processing_timestamp TIMESTAMP
        )
    ''')

    # Activity Logs table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS activity_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TIMESTAMP,
            user_id INTEGER,
            cooperative_name TEXT,
            action TEXT,
            details TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')

    # Pre-populate with default users if table is empty
    cursor.execute("SELECT COUNT(*) from users")
    if cursor.fetchone()[0] == 0:
        admin_password = hashlib.sha256("admin123".encode()).hexdigest()
        coop_password = hashlib.sha256("coop123".encode()).hexdigest()
        users_to_add = [
            ("admin", admin_password, "admin", "Farmers Payment Module Admin"),
            ("kcu", coop_password, "cooperative", "Kilimanjaro Cooperative Union"),
            ("mbeyacof", coop_password, "cooperative", "Mbeya Coffee Union"),
            ("dodoma_coop", coop_password, "cooperative", "Dodoma Grain Cooperative"),
            ("tanga_coop", coop_password, "cooperative", "Tanga Sisal Cooperative"),
            ("iringa_coop", coop_password, "cooperative", "Iringa Maize Cooperative"),
            ("morogoro_coop", coop_password, "cooperative", "Morogoro Rice Cooperative"),
            ("ruvuma_coop", coop_password, "cooperative", "Ruvuma Cashew Cooperative")
        ]
        for user in users_to_add:
            cursor.execute(
                "INSERT OR IGNORE INTO users (username, password, role, cooperative_name) VALUES (?, ?, ?, ?)", user)

    conn.commit()
    conn.close()


# --- Utility Functions ---
def log_activity(user_id, action, details=""):
    conn = sqlite3.connect('farmers_payment_module.db')
    cursor = conn.cursor()
    cursor.execute("SELECT cooperative_name FROM users WHERE id = ?", (user_id,))
    cooperative_name = cursor.fetchone()[0]
    cursor.execute(
        "INSERT INTO activity_logs (timestamp, user_id, cooperative_name, action, details) VALUES (?, ?, ?, ?, ?)",
        (datetime.now(), user_id, cooperative_name, action, details))
    conn.commit()
    conn.close()


def authenticate_user(username, password):
    conn = sqlite3.connect('farmers_payment_module.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id, password, role, cooperative_name FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    conn.close()
    if user and user[1] == hashlib.sha256(password.encode()).hexdigest():
        return {"id": user[0], "username": username, "role": user[2], "cooperative_name": user[3]}
    return None


# --- Layout Definitions ---
def create_login_layout():
    return dbc.Container([
        dbc.Row(dbc.Col(dbc.Card([
            dbc.CardBody([
                html.H2("Farmers Payment Module", className="text-center mb-4 text-success"),
                dbc.Input(id="login-username", placeholder="Username", type="text", className="mb-3"),
                dbc.Input(id="login-password", placeholder="Password", type="password", className="mb-3"),
                dbc.Button("Login", id="login-button", color="success", className="w-100"),
                html.Div(id="login-alert-placeholder", className="mt-3")
            ])
        ], className="shadow"), width=10, sm=8, md=6, lg=4), justify="center",
            className="min-vh-100 align-items-center"),

        dbc.Alert([
            html.H5("Demo Credentials", className="alert-heading"),
            html.P([html.B("Admin Account:")]),
            html.Ul([
                html.Li(["Username: ", html.Code("admin"), " | Password: ", html.Code("admin123")])
            ]),
            html.P([html.B("Cooperative Accounts:")]),
            html.Ul([
                html.Li(["Username: ", html.Code("kcu"), " | Password: ", html.Code("coop123")]),
                html.Li(["Username: ", html.Code("mbeyacof"), " | Password: ", html.Code("coop123")]),
                html.Li(["Username: ", html.Code("dodoma_coop"), " | Password: ", html.Code("coop123")]),
                html.Li(["Username: ", html.Code("tanga_coop"), " | Password: ", html.Code("coop123")]),
                html.Li(["Username: ", html.Code("iringa_coop"), " | Password: ", html.Code("coop123")]),
            ])
        ], color="info", style={"position": "absolute", "bottom": "10px", "left": "10px", "width": "auto"})
    ], fluid=True, className="bg-light")


# --- THIS FUNCTION HAS BEEN UPDATED ---
def create_cooperative_layout(session_data):
    return html.Div([
        dbc.NavbarSimple(brand=session_data.get('cooperative_name'),
                         children=[dbc.Button("Logout", id="logout-button", color="light", outline=True)],
                         color="success", dark=True),
        dbc.Container([
            dbc.Alert(id="coop-alert", is_open=False, duration=4000),
            html.H3("Farmer Data Submission  Portal", className="my-4"),
            dcc.Upload(id='upload-data', children=html.Div(['Drag and Drop or ', html.A('Select a CSV/Excel File')]),
                       style={'width': '100%', 'height': '60px', 'lineHeight': '60px', 'borderWidth': '1px',
                              'borderStyle': 'dashed', 'borderRadius': '5px', 'textAlign': 'center',
                              'margin': '10px 0'},
                       multiple=False),
            html.Div(id="submission-table-placeholder"),
            html.Hr(),

            dbc.Tabs(id="coop-tabs", active_tab="tab-coop-history", children=[
                dbc.Tab(label="📜 Submission History", tab_id="tab-coop-history", children=[
                    html.Div(id="coop-history-placeholder", className="py-4")
                ]),
                dbc.Tab(label="📊 Analytics", tab_id="tab-coop-analytics", children=[
                    html.Div(id="coop-analytics-content", className="py-4")
                ]),
            ]),
        ], fluid=True),
        dbc.Modal(id="coop-results-modal", size="xl", is_open=False)
    ])


def create_admin_layout(session_data):
    return html.Div([
        dbc.Toast(id="ipn-toast", is_open=False, duration=6000, icon="success",
                  style={"position": "fixed", "top": 20, "right": 20, "width": 350, "zIndex": 9999}),
        dbc.NavbarSimple(brand="Admin Payments Dashboard",
                         children=[dbc.Button("Logout", id="logout-button", color="light", outline=True)],
                         color="primary", dark=True),
        dbc.Container([
            html.Div(id="kpi-cards-placeholder"),
            html.Div(id="admin-dashboard-content"),
            html.Hr(),

            dbc.Tabs(id="admin-tabs", active_tab="tab-analytics", children=[
                dbc.Tab(label="📊 Analytics", tab_id="tab-analytics", children=[
                    html.Div(id="analytics-tab-content", className="py-4")
                ]),
                dbc.Tab(label="📄 Master Payment Data", tab_id="tab-master-data", children=[
                    html.Div(className="py-4", children=[
                        dbc.Collapse(html.Div(id="master-data-placeholder"), id="master-data-collapse", is_open=True)
                    ])
                ]),
                dbc.Tab(label="📜 Payment History", tab_id="tab-history", children=[
                    html.Div(className="py-4", children=[
                        dbc.Collapse(html.Div(id="payment-history-placeholder"), id="history-collapse", is_open=True)
                    ])
                ]),
                dbc.Tab(label="📝 User Activity Logs", tab_id="tab-logs", children=[
                    html.Div(className="py-4", children=[
                        dbc.Collapse(html.Div(id="activity-logs-placeholder"), id="logs-collapse", is_open=True)
                    ])
                ]),
            ]),
        ], fluid=True, className="py-4"),
        dbc.Modal(id="details-modal", size="xl", is_open=False),
        dbc.Modal([
            dbc.ModalHeader("Processing Payment"),
            dbc.ModalBody(id="payment-animation-placeholder"),
            dbc.ModalFooter(dbc.Button("Close", id="payment-close-button", color="secondary", disabled=True))
        ], id="payment-modal", backdrop="static")
    ])


# Main App Layout
app.layout = html.Div([
    dcc.Store(id="user-session", storage_type="session"),
    dcc.Store(id="batch-to-process"),
    dcc.Store(id='ipn-data-store'),
    dcc.Interval(id='payment-interval', interval=1500, n_intervals=0, disabled=True),
    dcc.Store(id='submission-trigger-store'),
    html.Div(id="main-content")
])


# --- Callbacks ---
@app.callback(
    Output("kpi-cards-placeholder", "children"),
    Input("user-session", "data"),
    Input("ipn-data-store", "data"),
    Input("submission-trigger-store", "data")
)
def update_kpi_cards(session_data, ipn_data, submission_trigger):
    if not session_data or session_data.get("role") != "admin":
        return None

    conn = sqlite3.connect('farmers_payment_module.db')
    cursor = conn.cursor()

    tmx_amount_received = 500000000
    cursor.execute("SELECT SUM(amount) FROM farmer_payments WHERE status = 'paid'")
    total_paid = cursor.fetchone()[0] or 0
    cursor.execute("SELECT COUNT(id) FROM farmer_payments WHERE status = 'paid'")
    farmers_paid_count = cursor.fetchone()[0] or 0
    cursor.execute("SELECT COUNT(id) FROM submission_batches WHERE status = 'pending_approval'")
    pending_submissions = cursor.fetchone()[0] or 0
    cursor.execute("SELECT COUNT(id) FROM users WHERE role = 'cooperative'")
    coop_count = cursor.fetchone()[0] or 0
    conn.close()

    tmx_card = dbc.Card(
        dbc.CardBody([
            html.P("Funds Received from TMX", className="card-text text-muted small"),
            html.H3(f"TSH {tmx_amount_received:,.2f}", className="card-title text-success"),
            html.P(f"Latest deposit received on {datetime.now().strftime('%Y-%m-%d')}", className="card-text"),
        ]),
        className="mb-4", style={"border-left": "5px solid #198754"}
    )
    kpi_cards = dbc.Row([
        dbc.Col(dbc.Card(dbc.CardBody([
            html.H4(f"TSH {total_paid:,.2f}", className="card-title"),
            html.P("Total Amount Paid", className="card-text text-muted"),
        ])), width=6, lg=3, className="mb-3"),
        dbc.Col(dbc.Card(dbc.CardBody([
            html.H4(f"{farmers_paid_count:,}", className="card-title"),
            html.P("Total Farmers Paid", className="card-text text-muted"),
        ])), width=6, lg=3, className="mb-3"),
        dbc.Col(dbc.Card(dbc.CardBody([
            html.H4(pending_submissions, className="card-title text-warning"),
            html.P("Pending Submissions", className="card-text text-muted"),
        ])), width=6, lg=3, className="mb-3"),
        dbc.Col(dbc.Card(dbc.CardBody([
            html.H4(coop_count, className="card-title"),
            html.P("Active Cooperatives", className="card-text text-muted"),
        ])), width=6, lg=3, className="mb-3"),
    ])
    return html.Div([tmx_card, kpi_cards])


@app.callback(Output("main-content", "children"), Input("user-session", "data"))
def display_page(session_data):
    if session_data:
        if session_data.get("role") == "admin":
            return create_admin_layout(session_data)
        elif session_data.get("role") == "cooperative":
            return create_cooperative_layout(session_data)
    return create_login_layout()


@app.callback(
    Output("user-session", "data"),
    Output("login-alert-placeholder", "children"),
    Input("login-button", "n_clicks"),
    State("login-username", "value"), State("login-password", "value"),
    prevent_initial_call=True
)
def handle_login(n_clicks, username, password):
    if not username or not password: return dash.no_update, dbc.Alert("Fields cannot be empty.", color="warning")
    user = authenticate_user(username, password)
    if user:
        log_activity(user['id'], 'Login', f"User '{user['username']}' logged in.")
        return user, None
    return None, dbc.Alert("Invalid credentials.", color="danger")


@app.callback(Output("user-session", "data", allow_duplicate=True), Input("logout-button", "n_clicks"),
              prevent_initial_call=True)
def handle_logout(n_clicks):
    if n_clicks: return None
    return dash.no_update


@app.callback(
    Output("submission-table-placeholder", "children"),
    Input('upload-data', 'contents'), State('upload-data', 'filename'),
    prevent_initial_call=True
)
def update_output(contents, filename):
    if contents is None: return html.Div()
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    try:
        df = pd.read_csv(io.StringIO(decoded.decode('utf-8'))) if 'csv' in filename else pd.read_excel(
            io.BytesIO(decoded))
        required_cols = {'farmer_name', 'bank_name', 'account_number', 'amount'}
        if not required_cols.issubset(df.columns): return dbc.Alert(
            f"File is missing columns: {required_cols - set(df.columns)}", color="danger")
        return html.Div([
            dcc.Store(id='submission-data', data={'df': df.to_dict('records'), 'filename': filename}),
            html.H5("Review Data"),
            dash_table.DataTable(id='editable-datatable', data=df.to_dict('records'),
                                 columns=[{'name': i, 'id': i} for i in df.columns], page_size=10,
                                 style_table={'overflowX': 'auto'}, editable=True),
            html.Hr(),
            dbc.Label("Note to Admin (Optional)", html_for="coop-note-textarea"),
            dbc.Textarea(id='coop-note-textarea', placeholder="Add notes for the admin regarding this submission...",
                         className="mb-3"),
            html.Div(dbc.Button("Submit to Admin", id="submit-to-admin-button", color="primary"),
                     className="d-flex justify-content-end")
        ])
    except Exception as e:
        return dbc.Alert(f"Error processing file: {e}", color="danger")


@app.callback(
    Output("coop-alert", "children"), Output("coop-alert", "is_open"), Output("coop-alert", "color"),
    Output("submission-table-placeholder", "children", allow_duplicate=True),
    Output("submission-trigger-store", "data"),
    Input("submit-to-admin-button", "n_clicks"),
    State("editable-datatable", "data"), State("submission-data", "data"), State("user-session", "data"),
    State("coop-note-textarea", "value"),
    prevent_initial_call=True
)
def submit_to_admin(n_clicks, table_data, submission_data_store, session_data, coop_note):
    if not n_clicks or not table_data: return "", False, "", dash.no_update, dash.no_update
    df = pd.DataFrame(table_data)
    filename = submission_data_store.get('filename', 'uploaded_file')
    conn = sqlite3.connect('farmers_payment_module.db')
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO submission_batches (cooperative_id, filename, record_count, total_amount, submission_timestamp, status, cooperative_notes) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (session_data['id'], filename, len(df), df['amount'].sum(), datetime.now(), 'pending_approval', coop_note))
        batch_id = cursor.lastrowid
        df_to_db = df[['farmer_name', 'bank_name', 'account_number', 'amount']]
        df_to_db['batch_id'] = batch_id
        df_to_db.to_sql('farmer_payments', conn, if_exists='append', index=False)
        conn.commit()
        log_activity(session_data['id'], 'Data Submission', f"Submitted '{filename}' with {len(df)} records.")
        msg, color = f"Successfully submitted {len(df)} records.", "success"
        return msg, True, color, html.Div(), datetime.now().isoformat()
    except Exception as e:
        conn.rollback();
        msg, color = f"Database error: {e}", "danger"
    finally:
        conn.close()
    return msg, True, color, dash.no_update, dash.no_update


@app.callback(
    Output("admin-dashboard-content", "children"),
    Input("user-session", "data"), Input("ipn-data-store", "data"), Input("submission-trigger-store", "data")
)
def render_admin_dashboard(session_data, ipn_data, submission_trigger):
    if not session_data or session_data.get("role") != "admin": return None
    conn = sqlite3.connect('farmers_payment_module.db')
    query = "SELECT b.id, u.cooperative_name, b.filename, b.record_count, b.total_amount FROM submission_batches b JOIN users u ON b.cooperative_id = u.id WHERE b.status = 'pending_approval' ORDER BY b.submission_timestamp DESC"
    batches_df = pd.read_sql_query(query, conn)
    conn.close()
    if batches_df.empty: return dbc.Alert("No pending submissions found.", color="info", className="m-4")
    cards = [dbc.Card([
        dbc.CardHeader(f"From: {row['cooperative_name']}"),
        dbc.CardBody([
            html.H5(row['filename'], className="card-title"),
            html.P(f"{row['record_count']} farmers, Total: TSH {row['total_amount']:,.2f}")
        ]),
        dbc.CardFooter(html.Div([
            dbc.Button("View Details", id={'type': 'view-details-btn', 'index': row['id']}, color="secondary"),
            dbc.Button("Pay Now", id={'type': 'pay-now-btn', 'index': row['id']}, color="success"),
        ], className="d-flex justify-content-between"))
    ], className="mb-3") for _, row in batches_df.iterrows()]
    return [html.H3("Pending Submissions", className="mb-4")] + cards


@app.callback(
    Output("details-modal", "is_open"), Output("details-modal", "children"),
    Input({'type': 'view-details-btn', 'index': ALL}, 'n_clicks'),
    prevent_initial_call=True
)
def toggle_details_modal(n_clicks):
    if not any(n_clicks): return False, None
    batch_id = int(eval(callback_context.triggered[0]['prop_id'].split('.')[0])['index'])
    conn = sqlite3.connect('farmers_payment_module.db')
    df = pd.read_sql_query(
        "SELECT farmer_name, bank_name, account_number, amount FROM farmer_payments WHERE batch_id = ?", conn,
        params=(batch_id,))
    notes_df = pd.read_sql_query("SELECT admin_notes, cooperative_notes FROM submission_batches WHERE id = ?", conn,
                                 params=(batch_id,))
    conn.close()
    admin_note, coop_note = notes_df['admin_notes'].iloc[0] or "", notes_df['cooperative_notes'].iloc[0]
    return True, [
        dbc.ModalHeader(f"Submission Details (Batch ID: {batch_id})"),
        dbc.ModalBody([
            dash_table.DataTable(data=df.to_dict('records'), columns=[{'name': i, 'id': i} for i in df.columns],
                                 style_table={'maxHeight': '40vh', 'overflowY': 'auto'}),
            html.Hr(),
            html.H5("Communication"),
            dbc.Label("Note from Cooperative:"),
            dbc.Alert(coop_note, color="info") if coop_note else html.P("No note provided.",
                                                                        className="text-muted fst-italic"),
            dbc.Label("Your Response to Cooperative:", className="mt-2"),
            dbc.Alert(id="note-save-alert", is_open=False, duration=3000),
            dcc.Textarea(id={'type': 'admin-note-textarea', 'index': batch_id}, value=admin_note,
                         style={'width': '100%', 'height': 100}),
            dbc.Button("Save Response", id={'type': 'save-note-btn', 'index': batch_id}, color="primary",
                       className="mt-2")
        ])
    ]


@app.callback(
    Output("note-save-alert", "is_open"), Output("note-save-alert", "children"), Output("note-save-alert", "color"),
    Input({'type': 'save-note-btn', 'index': ALL}, 'n_clicks'),
    State({'type': 'admin-note-textarea', 'index': ALL}, 'value'),
    prevent_initial_call=True
)
def save_admin_note(n_clicks, notes):
    if not any(n_clicks): return False, "", ""
    ctx = callback_context.triggered[0];
    batch_id = int(eval(ctx['prop_id'].split('.')[0])['index']);
    note_value = notes[0]
    try:
        conn = sqlite3.connect('farmers_payment_module.db');
        cursor = conn.cursor()
        cursor.execute("UPDATE submission_batches SET admin_notes = ? WHERE id = ?", (note_value, batch_id));
        conn.commit();
        conn.close()
        return True, "Response saved successfully!", "success"
    except Exception as e:
        return True, f"Error saving response: {e}", "danger"


@app.callback(
    Output("payment-modal", "is_open"), Output("payment-interval", "disabled"),
    Output("payment-animation-placeholder", "children"),
    Output("payment-close-button", "disabled"), Output("batch-to-process", "data"), Output("ipn-data-store", "data"),
    Input({'type': 'pay-now-btn', 'index': ALL}, 'n_clicks'), Input("payment-interval", "n_intervals"),
    Input("payment-close-button", "n_clicks"),
    State("batch-to-process", "data"), State("user-session", "data"),
    prevent_initial_call=True
)
def handle_payment_processing(pay_clicks, n_intervals, close_clicks, batch_id, session_data):
    ctx = callback_context
    if not ctx.triggered: return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update
    triggered_id_str = ctx.triggered[0]['prop_id'];
    triggered_value = ctx.triggered[0]['value']
    if 'pay-now-btn' in triggered_id_str and triggered_value is not None:
        id_dict = json.loads(triggered_id_str.split('.')[0]);
        new_batch_id = id_dict['index']
        animation_step = html.Div(
            [html.Div("🔄", style={'fontSize': 50}), dbc.Progress(value=5), html.P("Initiating...")],
            className="text-center")
        return True, False, animation_step, True, new_batch_id, dash.no_update
    elif 'payment-interval' in triggered_id_str and batch_id is not None:
        if n_intervals < 4:
            progress = (n_intervals + 1) * 25
            animation_step = html.Div(
                [html.Div("🔄", style={'fontSize': 50}), dbc.Progress(value=progress, striped=True, animated=True),
                 html.P("Processing...")], className="text-center")
            return True, False, animation_step, True, batch_id, dash.no_update
        else:
            conn = sqlite3.connect('farmers_payment_module.db');
            cursor = conn.cursor()
            cursor.execute(
                "SELECT u.cooperative_name, b.filename, b.record_count, b.total_amount FROM submission_batches b JOIN users u ON b.cooperative_id = u.id WHERE b.id = ?",
                (batch_id,))
            batch_info = cursor.fetchone()
            cursor.execute("UPDATE submission_batches SET status = 'processed' WHERE id = ?", (batch_id,))
            payments, success, failed = [], 0, 0;
            reasons = ["Invalid Account", "Bank Error", "Name Mismatch"]
            cursor.execute("SELECT id FROM farmer_payments WHERE batch_id = ?", (batch_id,))
            for (pid,) in cursor.fetchall():
                if random.random() < 0.95:
                    success += 1; payments.append(('paid', None, pid))
                else:
                    failed += 1; payments.append(('failed', random.choice(reasons), pid))
            cursor.executemany("UPDATE farmer_payments SET status = ?, failure_reason = ? WHERE id = ?", payments)
            if batch_info:
                coop_name, filename, record_count, total_amount = batch_info
                cursor.execute(
                    "INSERT INTO payment_history (batch_id, cooperative_name, filename, record_count, total_amount, processing_timestamp) VALUES (?, ?, ?, ?, ?, ?)",
                    (batch_id, coop_name, filename, record_count, total_amount, datetime.now()))
            conn.commit();
            conn.close()
            log_activity(session_data['id'], 'Payment Processed',
                         f"Processed '{batch_info[1]}' for {batch_info[0]}. Success: {success}, Failed: {failed}.")
            ipn = {'coop': batch_info[0], 'success': success, 'failed': failed, 'total': batch_info[2]}
            result = html.Div(
                [html.Div("✅", style={'fontSize': 60, 'color': 'green'}), dbc.Progress(value=100, color="success"),
                 html.H5("Payment Processed!")], className="text-center")
            return True, True, result, False, None, ipn
    elif 'payment-close-button' in triggered_id_str:
        return False, True, "", True, None, dash.no_update
    return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update


@app.callback(
    Output("ipn-toast", "is_open"), Output("ipn-toast", "header"), Output("ipn-toast", "children"),
    Output("ipn-toast", "icon"),
    Input("ipn-data-store", "data"), prevent_initial_call=True
)
def show_ipn_toast(data):
    if not data: return False, "", "", ""
    header, icon = "IPN: Transaction Complete", "warning" if data['failed'] > 0 else "success"
    body = f"{data['coop']}: Paid {data['success']}/{data['total']} farmers. ({data['failed']} failed)"
    return True, header, body, icon


# --- UPDATED COOPERATIVE CALLBACKS ---
@app.callback(
    Output("coop-history-placeholder", "children"),
    Input("coop-tabs", "active_tab"), Input("user-session", "data"), Input("coop-alert", "is_open")
)
def render_coop_history(active_tab, session_data, alert_is_open):
    if active_tab != "tab-coop-history" or not session_data or session_data.get("role") != "cooperative":
        return None
    conn = sqlite3.connect('farmers_payment_module.db')
    df = pd.read_sql_query(
        "SELECT id, filename, status, admin_notes, submission_timestamp FROM submission_batches WHERE cooperative_id = ? ORDER BY submission_timestamp DESC",
        conn, params=(session_data['id'],))
    conn.close()
    if df.empty: return dbc.Alert("No submissions yet.", color="info")
    return dbc.Accordion([
        dbc.AccordionItem([
            html.P(
                f"Submitted on: {datetime.strptime(row['submission_timestamp'].split('.')[0], '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d %I:%M %p')}"),
            dbc.Alert(f"Admin Response: {row['admin_notes']}", color="info") if row['admin_notes'] else "",
            dbc.Button("View Results", id={'type': 'view-results-btn', 'index': row['id']}) if row[
                                                                                                   'status'] == 'processed' else ""
        ], title=html.Div([row['filename'], dbc.Badge(row['status'].replace('_', ' ').title(), className="ms-2",
                                                      color="success" if row['status'] == 'processed' else "warning")]))
        for _, row in df.iterrows()
    ], start_collapsed=True)


@app.callback(
    Output('coop-results-modal', 'is_open'), Output('coop-results-modal', 'children'),
    Input({'type': 'view-results-btn', 'index': ALL}, 'n_clicks'), prevent_initial_call=True
)
def show_coop_results_modal(n_clicks):
    if not any(n_clicks): return False, None
    batch_id = int(eval(callback_context.triggered[0]['prop_id'].split('.')[0])['index'])
    conn = sqlite3.connect('farmers_payment_module.db')
    df = pd.read_sql_query(
        "SELECT farmer_name, bank_name, account_number, amount, status, failure_reason FROM farmer_payments WHERE batch_id = ?",
        conn, params=(batch_id,))
    conn.close()
    return True, [
        dbc.ModalHeader(f"Payment Results (Batch ID: {batch_id})"),
        dbc.ModalBody(dash_table.DataTable(
            data=df.to_dict('records'), columns=[{'name': i.replace('_', ' ').title(), 'id': i} for i in df.columns],
            style_table={'overflowX': 'auto'}, editable=False,
            style_data_conditional=[{'if': {'filter_query': '{status} = "paid"'}, 'backgroundColor': '#d4edda'},
                                    {'if': {'filter_query': '{status} = "failed"'}, 'backgroundColor': '#f8d7da'}]
        ))
    ]


# --- ADMIN TAB CALLBACKS ---
@app.callback(Output("payment-history-placeholder", "children"), Input("admin-tabs", "active_tab"),
              Input("ipn-data-store", "data"))
def render_payment_history(active_tab, ipn_data):
    if active_tab != "tab-history": return None
    conn = sqlite3.connect('farmers_payment_module.db')
    df = pd.read_sql_query("SELECT * FROM payment_history ORDER BY processing_timestamp DESC", conn)
    conn.close()
    if df.empty: return dbc.Alert("No processed payments found.", color="secondary")
    df['processing_timestamp'] = pd.to_datetime(df['processing_timestamp']).dt.strftime('%Y-%m-%d %I:%M:%S %p')
    cooperatives = sorted(df['cooperative_name'].unique())
    colors = ['#E6E6FA', '#FFF0F5', '#F0FFF0', '#F5FFFA', '#F0F8FF', '#F8F8FF', '#FFF5EE', '#FAFAD2']
    color_map = {coop: colors[i % len(colors)] for i, coop in enumerate(cooperatives)}
    style_data_conditional = [
        {'if': {'filter_query': f'{{cooperative_name}} = "{coop_name}"'}, 'backgroundColor': color} for coop_name, color
        in color_map.items()]
    return dash_table.DataTable(data=df.to_dict('records'),
                                columns=[{'name': i.replace('_', ' ').title(), 'id': i} for i in df.columns],
                                page_size=10, style_table={'overflowX': 'auto'}, editable=False,
                                style_data_conditional=style_data_conditional)


@app.callback(Output("activity-logs-placeholder", "children"), Input("admin-tabs", "active_tab"),
              Input("ipn-data-store", "data"))
def render_activity_logs(active_tab, ipn_data):
    if active_tab != "tab-logs": return None
    conn = sqlite3.connect('farmers_payment_module.db')
    df = pd.read_sql_query(
        "SELECT timestamp, cooperative_name, action, details FROM activity_logs ORDER BY timestamp DESC", conn)
    conn.close()
    if df.empty: return dbc.Alert("No user activity found.", color="secondary")
    df['timestamp'] = pd.to_datetime(df['timestamp']).dt.strftime('%Y-%m-%d %I:%M:%S %p')
    return dash_table.DataTable(data=df.to_dict('records'),
                                columns=[{'name': i.replace('_', ' ').title(), 'id': i} for i in df.columns],
                                page_size=10, style_table={'overflowX': 'auto'}, editable=False,
                                style_cell={'whiteSpace': 'normal', 'height': 'auto', 'textAlign': 'left'})


@app.callback(Output("master-data-placeholder", "children"), Input("admin-tabs", "active_tab"),
              Input("ipn-data-store", "data"))
def render_master_data_table(active_tab, ipn_data):
    if active_tab != "tab-master-data": return None
    conn = sqlite3.connect('farmers_payment_module.db')
    query = """
        SELECT u.cooperative_name, b.submission_timestamp, b.filename, p.* FROM farmer_payments AS p
        JOIN submission_batches AS b ON p.batch_id = b.id JOIN users AS u ON b.cooperative_id = u.id
        ORDER BY b.submission_timestamp DESC;"""
    try:
        df = pd.read_sql_query(query, conn)
    finally:
        conn.close()
    if df.empty: return dbc.Alert("No cooperative data has been submitted yet.", color="secondary")
    df['submission_timestamp'] = pd.to_datetime(df['submission_timestamp']).dt.strftime('%Y-%m-%d %I:%M %p')
    cooperatives = sorted(df['cooperative_name'].unique())
    colors = ['#E6E6FA', '#FFF0F5', '#F0FFF0', '#F5FFFA', '#F0F8FF', '#F8F8FF', '#FFF5EE', '#FAFAD2']
    color_map = {coop: colors[i % len(colors)] for i, coop in enumerate(cooperatives)}
    style_data_conditional = [
        {'if': {'filter_query': f'{{cooperative_name}} = "{coop_name}"'}, 'backgroundColor': color} for coop_name, color
        in color_map.items()]
    return dash_table.DataTable(data=df.to_dict('records'),
                                columns=[{'name': col.replace('_', ' ').title(), 'id': col} for col in df.columns],
                                page_size=15, style_table={'overflowX': 'auto'},
                                style_cell={'textAlign': 'left', 'whiteSpace': 'normal', 'height': 'auto'},
                                filter_action="native", sort_action="native",
                                sort_by=[{'column_id': 'submission_timestamp', 'direction': 'desc'}],
                                style_data_conditional=style_data_conditional)


@app.callback(Output("analytics-tab-content", "children"), Input("admin-tabs", "active_tab"),
              Input("ipn-data-store", "data"))
def render_analytics_tab(active_tab, ipn_data):
    if active_tab != "tab-analytics": return None
    conn = sqlite3.connect('farmers_payment_module.db')
    query = "SELECT b.submission_timestamp, u.cooperative_name, p.farmer_name, p.bank_name, p.amount, p.status FROM farmer_payments p JOIN submission_batches b ON p.batch_id = b.id JOIN users u ON b.cooperative_id = u.id"
    try:
        df = pd.read_sql_query(query, conn)
    finally:
        conn.close()
    if df.empty: return dbc.Alert("No data available to generate analytics.", color="info")
    df['date'] = pd.to_datetime(df['submission_timestamp']).dt.date;
    df_paid = df[df['status'] == 'paid']
    bank_activity = df_paid.groupby('bank_name').agg(total_amount=('amount', 'sum'), account_holders=(
    'farmer_name', 'nunique')).reset_index().sort_values('total_amount', ascending=False)
    coop_activity = df_paid.groupby('cooperative_name').agg(total_amount=('amount', 'sum'),
                                                            members=('farmer_name', 'nunique')).reset_index()
    farmer_activity = df_paid.groupby('farmer_name').agg(total_amount=('amount', 'sum'),
                                                         transaction_count=('farmer_name', 'count')).reset_index()
    top_farmers_value = farmer_activity.sort_values('total_amount', ascending=False).head(10)
    top_farmers_busy = farmer_activity.sort_values('transaction_count', ascending=False).head(10)
    daily_trends = df_paid.groupby('date').agg(total_amount=('amount', 'sum'),
                                               unique_banks=('bank_name', 'nunique')).reset_index()
    status_distribution = df.groupby(['date', 'status'])['status'].count().unstack(fill_value=0).reset_index();
    status_distribution = pd.melt(status_distribution, id_vars=['date'], value_vars=['paid', 'failed'])
    fig_bank_amount = px.bar(bank_activity.head(10), x='bank_name', y='total_amount',
                             title='Top 10 Banks by Transaction Value',
                             labels={'bank_name': 'Bank', 'total_amount': 'Total Amount (TSH)'})
    fig_bank_holders = px.bar(bank_activity.sort_values('account_holders', ascending=False).head(10), x='bank_name',
                              y='account_holders', title='Top 10 Banks by Unique Farmers',
                              labels={'bank_name': 'Bank', 'account_holders': 'Number of Farmers'})
    fig_coop_value = px.pie(coop_activity, names='cooperative_name', values='total_amount',
                            title='Transaction Value by Cooperative')
    fig_coop_members = px.pie(coop_activity, names='cooperative_name', values='members',
                              title='Unique Farmers by Cooperative')
    fig_daily_trend = px.line(daily_trends, x='date', y='total_amount', title='Daily Transaction Volume (Amount)',
                              markers=True)
    fig_status_dist = px.bar(status_distribution, x='date', y='value', color='status',
                             title='Paid vs. Failed Transactions Over Time', barmode='stack',
                             color_discrete_map={'paid': 'green', 'failed': 'red'})
    return html.Div([dbc.Row([dbc.Col(dcc.Graph(figure=fig_daily_trend), width=12)]), html.Hr(),
                     dbc.Row([dbc.Col(dcc.Graph(figure=fig_status_dist), width=12)]), html.Hr(), dbc.Row(
            [dbc.Col(dcc.Graph(figure=fig_bank_amount), md=6), dbc.Col(dcc.Graph(figure=fig_bank_holders), md=6)]),
                     html.Hr(), dbc.Row(
            [dbc.Col(dcc.Graph(figure=fig_coop_value), md=6), dbc.Col(dcc.Graph(figure=fig_coop_members), md=6)]),
                     html.Hr(), dbc.Row([dbc.Col([html.H5("Top 10 Most Valuable Farmers"),
                                                  dash_table.DataTable(data=top_farmers_value.to_dict('records'),
                                                                       columns=[{'name': i.replace('_', ' ').title(),
                                                                                 'id': i} for i in
                                                                                top_farmers_value.columns],
                                                                       style_table={'overflowX': 'auto'})], md=6),
                                         dbc.Col([html.H5("Top 10 Busiest Farmers (by # of payments)"),
                                                  dash_table.DataTable(data=top_farmers_busy.to_dict('records'),
                                                                       columns=[{'name': i.replace('_', ' ').title(),
                                                                                 'id': i} for i in
                                                                                top_farmers_busy.columns],
                                                                       style_table={'overflowX': 'auto'})], md=6)])])


# --- NEW CALLBACK FOR COOPERATIVE ANALYTICS TAB ---
@app.callback(
    Output("coop-analytics-content", "children"),
    Input("coop-tabs", "active_tab"),
    Input("user-session", "data"),
    Input("coop-alert", "is_open")  # Refresh on new submission
)
def render_cooperative_analytics(active_tab, session_data, alert_is_open):
    if active_tab != "tab-coop-analytics" or not session_data or session_data.get("role") != "cooperative":
        return None

    coop_id = session_data.get('id')
    conn = sqlite3.connect('farmers_payment_module.db')
    query = """
        SELECT b.submission_timestamp, p.farmer_name, p.bank_name, p.amount, p.status FROM farmer_payments AS p
        JOIN submission_batches AS b ON p.batch_id = b.id WHERE b.cooperative_id = ?;
    """
    try:
        df = pd.read_sql_query(query, conn, params=(coop_id,))
    finally:
        conn.close()

    if df.empty:
        return dbc.Alert("You have not submitted any data yet. No analytics to display.", color="info")

    df['date'] = pd.to_datetime(df['submission_timestamp']).dt.date
    df_paid = df[df['status'] == 'paid'].copy()

    # KPIs
    total_submitted_amount = df['amount'].sum()
    total_paid_amount = df_paid['amount'].sum()
    total_farmers_paid = df_paid['farmer_name'].count()
    success_rate = (total_farmers_paid / len(df)) * 100 if len(df) > 0 else 0

    kpi_cards = dbc.Row([
        dbc.Col(dbc.Card(dbc.CardBody(
            [html.H4(f"TSH {total_submitted_amount:,.2f}"), html.P("Total Amount Submitted", className="text-muted")])),
                md=3),
        dbc.Col(dbc.Card(dbc.CardBody(
            [html.H4(f"TSH {total_paid_amount:,.2f}"), html.P("Total Amount Paid", className="text-muted")])), md=3),
        dbc.Col(dbc.Card(dbc.CardBody(
            [html.H4(f"{total_farmers_paid:,}"), html.P("Farmers Paid Successfully", className="text-muted")])), md=3),
        dbc.Col(dbc.Card(
            dbc.CardBody([html.H4(f"{success_rate:.2f}%"), html.P("Payment Success Rate", className="text-muted")])),
                md=3),
    ])

    # Calculations
    status_counts = df['status'].value_counts().reset_index()
    status_counts.columns = ['status', 'count']
    bank_dist = df_paid['bank_name'].value_counts().reset_index().head(10)
    bank_dist.columns = ['bank_name', 'count']
    daily_submission_trend = df.groupby('date')['amount'].sum().reset_index()
    farmer_activity = df_paid.groupby('farmer_name').agg(total_amount=('amount', 'sum'),
                                                         payment_count=('farmer_name', 'count')).reset_index()
    top_farmers_value = farmer_activity.sort_values('total_amount', ascending=False).head(10)

    # Figures
    fig_status = px.pie(status_counts, names='status', values='count', title='Payment Status Distribution',
                        color='status', color_discrete_map={'paid': 'green', 'failed': 'red'})
    fig_banks = px.bar(bank_dist, x='bank_name', y='count', title='Top 10 Banks Used by Your Farmers')
    fig_daily = px.line(daily_submission_trend, x='date', y='amount', title='Your Daily Submission Value (TSH)',
                        markers=True)

    return html.Div([
        kpi_cards,
        html.Hr(),
        dbc.Row([
            dbc.Col(dcc.Graph(figure=fig_status), md=6),
            dbc.Col(dcc.Graph(figure=fig_banks), md=6),
        ]),
        html.Hr(),
        dbc.Row([
            dbc.Col(dcc.Graph(figure=fig_daily), md=12),
        ]),
        html.Hr(),
        dbc.Row([
            dbc.Col([
                html.H5("Your Top 10 Most Valuable Farmers"),
                dash_table.DataTable(data=top_farmers_value.to_dict('records'),
                                     columns=[{'name': i.replace('_', ' ').title(), 'id': i} for i in
                                              top_farmers_value.columns], style_table={'overflowX': 'auto'})
            ], md=12),
        ]),
    ])


# --- Run Application ---
if __name__ == "__main__":
    init_db()
    app.run(debug=True, port=8055)