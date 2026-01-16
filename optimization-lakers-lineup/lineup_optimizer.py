import pandas as pd
import gurobipy as gp
from gurobipy import GRB
import os

# --- CONFIGURATION LOADER ---
# This dictionary will be populated from the CSV file
PLAY_CONFIGS = {}

def load_play_configs(csv_path="play_configs.csv"):
    """
    Loads play configurations from a CSV file into the global PLAY_CONFIGS dictionary.
    """
    global PLAY_CONFIGS
    
    # Check if file exists to prevent crashing on import
    if not os.path.exists(csv_path):
        print(f"[WARNING] Config file '{csv_path}' not found. PLAY_CONFIGS is empty.")
        return

    try:
        df = pd.read_csv(csv_path)
        
        # Validation: Ensure required identifier column exists
        if 'play_name' not in df.columns:
             print("[ERROR] Config CSV must have a 'play_name' column.")
             return
        
        # Convert to dictionary format: { "PlayName": { "Role": Count, ... } }
        df.set_index('play_name', inplace=True)
        PLAY_CONFIGS = df.to_dict(orient='index')
        print(f"Loaded {len(PLAY_CONFIGS)} plays from {csv_path}")
        
    except Exception as e:
        print(f"[ERROR] Failed to load play configs: {e}")

# Automatically attempt to load configs when this module is imported
load_play_configs()

# --- OPTIMIZATION FUNCTIONS ---

def load_and_process_data(excel_path, selected_play):
    """
    Ingests the master CSV and filters/reshapes it for the optimization model.
    """
    df_play_data = pd.read_excel(excel_path, sheet_name='play_data', index_col=0)
    df_chem=pd.read_excel(excel_path, sheet_name = 'chemistry', index_col=0)
    
    # 1. Parse Player Data for the selected play
    # Filter for 'PlayerPlay' rows and the specific play selected
    play_mask = (df_play_data['play_name'] == selected_play)
    df_play = df_play_data[play_mask].set_index('player_name')
    
    if df_play.empty:
        raise ValueError(f"No data found for play: {selected_play}")

    # Extract Players List
    players = df_play.index.tolist()
    
    # 2. Extract Parameters
    # Offensive PPP for this specific play
    O_p = df_play['O_ppp'].to_dict()
    
    # Defensive Roles (Columns starting with D_)
    d_cols = [c for c in df_play_data.columns if c.startswith('D_')]
    # Dict: {Player: {Role: Value}}
    D_ik = df_play[d_cols].to_dict(orient='index')
    
    # Offensive Roles (Columns starting with V_)
    o_cols = [c for c in df_play_data.columns if c.startswith('V_')]
    # Dict: {Player: {Role: Value}}
    V_ir = df_play[o_cols].to_dict(orient='index')
    
    C_ij = {}
    # Initialize all pairs to 0.0 first
    for p1 in players:
        for p2 in players:
            if p1 < p2:
                C_ij[(p1, p2)] = 0.0
                
    # Fill in from CSV
    for _, row in df_chem.iterrows():
        p1 = row['player_name']
        p2 = row['chemistry_with_name']
        val = row['C_bonus']
        
        # Ensure p1, p2 are in our active player list and ordered correctly for the key
        if p1 in players and p2 in players:
            key = tuple(sorted((p1, p2)))
            C_ij[key] = val

    return players, d_cols, o_cols, O_p, D_ik, V_ir, C_ij

def solve_lineup_optimization(excel_path, selected_play, outputFile):
    print(f"\n--- OPTIMIZING FOR PLAY: {selected_play} ---")
    
    # 1. Load Data
    try:
        players, d_roles, o_roles, O_p, D_ik, V_ir, C_ij = load_and_process_data(excel_path, selected_play)
    except ValueError as e:
        print(e)
        return

    # 2. Get Requirements for this play
    if selected_play not in PLAY_CONFIGS:
        print(f"Error: No role configuration defined for {selected_play}")
        return
    required_roles = PLAY_CONFIGS[selected_play]

    # 3. Build Model
    m = gp.Model("Lakers_Advanced")
    m.setParam('OutputFlag', 0)

    # Variables
    x = m.addVars(players, vtype=GRB.BINARY, name="X") # Player selected
    z = m.addVars(players, d_roles, vtype=GRB.BINARY, name="Z") # Def Role
    a = m.addVars(players, o_roles, vtype=GRB.BINARY, name="A") # Off Role
    y = m.addVars(C_ij.keys(), vtype=GRB.BINARY, name="Y") # Chemistry

    # Objective: Maximize Net Rating
    # Note: We subtract Defense (lower is better) and add Chemistry/Role Value (can be negative now)
    obj = (
        gp.quicksum(O_p[i] * x[i] for i in players) - 
        gp.quicksum(D_ik[i][k] * z[i,k] for i in players for k in d_roles) +
        gp.quicksum(C_ij[pair] * y[pair] for pair in C_ij) + 
        gp.quicksum(V_ir[i][r] * a[i,r] for i in players for r in o_roles)
    )
    m.setObjective(obj, GRB.MAXIMIZE)

    # Constraints
    
    # 1. Five Players on court
    m.addConstr(x.sum() == 5, "Five_Players")

    # 2. Chemistry Logic (Linearization)
    for (p1, p2) in C_ij:
        m.addConstr(y[p1, p2] <= x[p1])
        m.addConstr(y[p1, p2] <= x[p2])
        m.addConstr(y[p1, p2] >= x[p1] + x[p2] - 1)

    # 3. Defensive Roles
    # Each player needs exactly 1 defensive role if playing
    for i in players:
        m.addConstr(z.sum(i, '*') == x[i])
    # Each defensive role needs exactly 1 player
    for k in d_roles:
        m.addConstr(z.sum('*', k) == 1)

    # 4. Offensive Roles (Strict Composition)
    # Player can have max 1 offensive role
    for i in players:
        m.addConstr(a.sum(i, '*') == x[i]) # Must have a role if playing
        
    # Team must exactly match the play requirements
    for r, count in required_roles.items():
        m.addConstr(a.sum('*', r) == count, f"Req_{r}")

    # 4. Solve
    m.optimize()

    #create dfs for storing optimal values
    ppp_df = pd.DataFrame(columns = ['Defensive_Role', 'Offensive_Role', 'Offensive PPP',\
                                                                                    'Role_Bonus', 'Defensive_PPP', 'Net_Contribution'])
    chem_df = pd.DataFrame(columns = ['Chemistry_Bonus'])

    optimal_df = pd.DataFrame(columns = ['Value'])

    # 5. Output
    
    print(f"Expected Net Points: {m.ObjVal:.3f}")
    optimal_df.loc['Expected Net Points'] = m.ObjVal
    selected = [p for p in players if x[p].X > 0.5]
    
    # Helper to find which role a player has
    def get_role(p_name, var_dict, roles):
        for r in roles:
            if var_dict[p_name, r].X > 0.5:
                return r
        return "None"

    print(f"{'PLAYER':<20} {'DEF ROLE':<20} {'OFF ROLE':<20} {'OFF PPP':<10} {'ROLE VAL':<10} {'DEF PPP':<10} {'TOTAL PPP':<6}")
    print("-" * 105)

    for p in selected:
        d_role = get_role(p, z, d_roles)
        o_role = get_role(p, a, o_roles)
        
        # Formatting checks
        o_ppp_val = O_p[p]
        v_val = V_ir[p][o_role]
        d_val = D_ik[p][d_role]
        total_val = o_ppp_val + v_val - d_val
        
        ppp_df.loc[p] = [d_role, o_role, o_ppp_val, v_val, d_val, total_val]

        print(f"{p:<20} {d_role:<20} {o_role:<22} {o_ppp_val:<10.2f} {v_val:<10.2f} {d_val:<10.2f} {total_val:<6.2f}")
        
    print("-" * 105)
    # Check for negative chemistry in the solution
    print("Active Chemistry Pairs:")
    total_chem = 0
    for (p1, p2), val in C_ij.items():
        if y[p1, p2].X > 0.5:
            status = "(NEGATIVE)" if val < 0 else ""
            print(f"  {p1} + {p2}: {val} {status}")
            total_chem += val
            chem_df.loc[f'{p1}, {p2}'] = val
    print(f"Total Chemistry Impact: {total_chem:.3f}")

    writer = pd.ExcelWriter(outputFile)
    ppp_df.to_excel(writer, sheet_name = 'player_roles')
    chem_df.to_excel(writer, sheet_name='chemistry_bonuses')
    optimal_df.to_excel(writer, sheet_name='total_expected_value')
    writer.close()