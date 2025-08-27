import math
import streamlit as st

st.set_page_config(page_title="Pump Power Calculator", page_icon="💧", layout="centered")

# ----------------------------
# Helpers
# ----------------------------
G_SI = 9.80665  # m/s^2
RHO_WATER_4C = 1000.0  # kg/m^3 (reference for SG)

FLOW_UNITS = {
    "m³/s": 1.0,
    "L/s": 1e-3,
    "L/min": 1e-3 / 60.0,
    "m³/h": 1.0 / 3600.0,
    "gpm (US)": 0.003785411784 / 60.0,  # 1 US gallon = 3.785411784 L
    "ft³/s": 0.028316846592,
}

HEAD_UNITS = {
    "m": 1.0,
    "ft": 0.3048,
}

EFF_UNITS = {
    "%": 0.01,
    "fraction": 1.0,
}

def to_si_flow(value, unit):
    return value * FLOW_UNITS[unit]

def to_si_head(value, unit):
    return value * HEAD_UNITS[unit]

def to_fraction(value, unit):
    return max(1e-6, min(0.999999, value * EFF_UNITS[unit]))

def sg_to_density(sg):
    return max(1e-6, sg) * RHO_WATER_4C

def hydraulic_power_kw(rho, g, Q, H):
    # P_h = rho * g * Q * H  [W]
    return (rho * g * Q * H) / 1000.0

def shaft_power_kw(P_h_kw, eff_frac):
    return P_h_kw / eff_frac

def kw_to_hp(kw):
    return kw * 1.34102209  # metric HP

# ----------------------------
# UI
# ----------------------------
st.title("💧 Pump Power Calculator")
st.caption("Compute hydraulic and shaft power for a centrifugal/rotodynamic pump. Supports SI & US units, any fluid via specific gravity.")

with st.sidebar:
    st.header("Inputs")
    st.markdown("**Flow rate**")
    Q_val = st.number_input("Flow value", min_value=0.0, value=0.05, step=0.01)
    Q_unit = st.selectbox("Flow unit", list(FLOW_UNITS.keys()), index=0)

    st.markdown("**Total dynamic head (TDH)**")
    H_val = st.number_input("Head value", min_value=0.0, value=20.0, step=0.5)
    H_unit = st.selectbox("Head unit", list(HEAD_UNITS.keys()), index=0)

    st.markdown("**Fluid**")
    sg = st.number_input("Specific Gravity (SG)", min_value=0.0, value=1.0, step=0.05,
                         help="SG = ρ_fluid / ρ_water. Water ≈ 1.00, seawater ≈ 1.025, oils < 1, etc.")
    rho_override = st.checkbox("Override with custom density (kg/m³)")
    rho_custom = st.number_input("Custom density (kg/m³)", min_value=0.0, value=1000.0, step=10.0, disabled=not rho_override)

    st.markdown("**Pump/Drive**")
    eff_val = st.number_input("Pump efficiency", min_value=0.0, value=70.0, step=1.0)
    eff_unit = st.selectbox("Efficiency unit", ["%", "fraction"], index=0)

    st.markdown("---")
    st.markdown("**Advanced**")
    g_val = st.number_input(
        "Gravity g (m/s²)",
        min_value=0.0,
        value=G_SI,
        step=0.001,
        format="%.3f",   # 🔹 show 3 decimal places
        help="Use 9.81 m/s² for standard Earth gravity."
    )
    show_steps = st.checkbox("Show calculation steps", value=True)

# Convert inputs to SI
Q_si = to_si_flow(Q_val, Q_unit)            # m³/s
H_si = to_si_head(H_val, H_unit)            # m
eta = to_fraction(eff_val, eff_unit)        # fraction
rho = rho_custom if rho_override else sg_to_density(sg)

# Calculations
P_h_kw = hydraulic_power_kw(rho, g_val, Q_si, H_si)
P_shaft_kw = shaft_power_kw(P_h_kw, eta)
P_h_hp = kw_to_hp(P_h_kw)
P_shaft_hp = kw_to_hp(P_shaft_kw)

# Output
st.subheader("Results")
c1, c2 = st.columns(2)
with c1:
    st.metric("Hydraulic Power", f"{P_h_kw:,.3f} kW", help="Power imparted to the fluid.")
    st.metric("Hydraulic Power", f"{P_h_hp:,.3f} HP")
with c2:
    st.metric("Shaft Power", f"{P_shaft_kw:,.3f} kW", help="Power at the pump shaft (before motor/drive losses).")
    st.metric("Shaft Power", f"{P_shaft_hp:,.3f} HP")

st.divider()

# Quick notes
with st.expander("Assumptions & Notes", expanded=False):
    st.markdown(
        """
- **Formulae**  
  - Hydraulic power:  \n
    \\(P_{hyd} = \\rho\\, g\\, Q\\, H\\)  
  - Shaft power:  \n
    \\(P_{shaft} = \\dfrac{P_{hyd}}{\\eta}\\)
- **Units**: Internally, the app converts flow to m³/s and head to meters.
- **Specific Gravity (SG)** converts to density by \\(\\rho = SG \\cdot 1000\\,\\text{kg/m³}\\).
- **Efficiency** is the pump hydraulic efficiency (not motor efficiency).  
- For a **motor** selection, you may want to add motor efficiency and a service factor.
        """
    )

if show_steps:
    st.subheader("Calculation Steps")
    st.latex(r"Q_{SI} = Q \times \text{(flow unit factor)} \quad [\text{m}^3/\text{s}]")
    st.latex(r"H_{SI} = H \times \text{(head unit factor)} \quad [\text{m}]")
    st.latex(r"\rho = \begin{cases}"
             r"\rho_{\text{custom}} & \text{if custom density is used} \\"
             r"\text{SG} \times 1000 & \text{otherwise}"
             r"\end{cases}")
    st.latex(r"P_{hyd} = \rho \, g \, Q_{SI} \, H_{SI} \quad [\text{W}]")
    st.latex(r"P_{shaft} = \dfrac{P_{hyd}}{\eta}")
    with st.container(border=True):
        st.code(
f"""Given:
    Flow = {Q_val} {Q_unit}  -> Q_SI = {Q_si:.6f} m³/s
    Head = {H_val} {H_unit}  -> H_SI = {H_si:.6f} m
    Specific Gravity = {sg:.4f}
    Density used = {rho:.2f} kg/m³ (custom override = {rho_override})
    g = {g_val:.3f} m/s²
    Efficiency = {eff_val} {eff_unit} -> η = {eta:.6f}

Computed:
    Hydraulic Power = ρ·g·Q·H = {P_h_kw:.6f} kW = {P_h_hp:.6f} HP
    Shaft Power     = P_h / η  = {P_shaft_kw:.6f} kW = {P_shaft_hp:.6f} HP
""",
        language="text",
        )

st.divider()
st.caption("© Pump Power Calculator • Streamlit • No external APIs • Suitable for Hugging Face Spaces")
