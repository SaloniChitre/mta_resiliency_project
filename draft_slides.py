from fpdf import FPDF
from fpdf.enums import XPos, YPos
import os

class MTASlides(FPDF):
    def header(self):
        # Professional Dark Header
        self.set_fill_color(33, 37, 41) 
        self.rect(0, 0, 297, 25, 'F') 
        self.set_font('Helvetica', 'B', 16)
        self.set_text_color(255, 255, 255)
        self.set_y(8)
        self.cell(0, 10, self.title_text, align='L', new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    def footer(self):
        self.set_y(-15)
        self.set_font('Helvetica', 'I', 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, f'NYC Resilience Digital Twin | Draft Submission | Page {self.page_no()}', align='R')

    def add_content_slide(self, title, bullet_points, image_path=None):
        self.title_text = title
        self.add_page()
        self.set_y(35)
        
        # Text Body
        self.set_font('Helvetica', '', 11)
        self.set_text_color(40, 40, 40)
        for point in bullet_points:
            # SAFETY: Clean Unicode characters like smart quotes or bullet points
            clean_point = point.replace('\u2019', "'").replace('\u2013', "-").replace('\u2022', "-")
            self.multi_cell(130, 8, f"- {clean_point}")
            self.ln(2)
        
        # High-res Visuals
        if image_path and os.path.exists(image_path):
            self.image(image_path, x=145, y=35, w=140)

def generate_10_page_deck():
    pdf = MTASlides(orientation='L', unit='mm', format='A4')
    
    # 1. TITLE PAGE
    pdf.title_text = "MTA Resiliency Digital Twin (Project Nova)"
    pdf.add_page()
    pdf.set_y(80)
    pdf.set_font('Helvetica', 'B', 24)
    pdf.cell(0, 10, "MTA Resiliency Digital Twin", align='C', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font('Helvetica', '', 14)
    pdf.cell(0, 10, "Predicting Systemic Infrastructure Collapse via Graph Theory", align='C', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(10)
    pdf.set_font('Helvetica', 'I', 12)
    pdf.cell(0, 10, "Author: Saloni Chitre | Advisor: Kimberly Brazaitis", align='C')

    # 2. PROBLEM STATEMENT
    pdf.add_content_slide("01: The Vulnerability Problem", [
        "NYC's aging subway infrastructure faces 100-year storm events annually.",
        "Flash flooding causes immediate track isolation (Edges) and station failure (Nodes).",
        "Current MTA monitoring is reactive, leading to trapped passengers and system lockups."
    ], "plots/temp/map_risk.png")

    # 3. DATA ARCHITECTURE
    pdf.add_content_slide("02: Data Ingestion & Cleaning", [
        "Source: MTA New York City Transit GTFS Real-time & Static feeds.",
        "Preprocessing: Deduplicated 470+ unique stop_ids in cleaned_hubs.csv.",
        "Normalization: Coordinate standardization for 1:1 spatial accuracy.",
        "Edge Weighting: Assigned initial flood thresholds to 1,000+ track segments."
    ])

    # 4. GRAPH THEORY FRAMEWORK
    pdf.add_content_slide("03: Modeling the Digital Twin", [
        "NetworkX Implementation: Modeled as a Directed Multigraph.",
        "Node Attributes: Connectivity degree, station depth, and hub importance.",
        "Edge Attributes: 'flood_intensity' as the primary trigger variable.",
        "Topology: Captures physical track dependencies across all 5 boroughs."
    ], "plots/temp/map_graph.png")

    # 5. THE NODE-X TRIGGER LOGIC
    pdf.add_content_slide("04: Predictive Cascade Algorithm", [
        "Algorithm: Custom 'Orphan Effect' recursive logic.",
        "Functional Failure: A node fails if its entrance edges are severed.",
        "Dependency Mapping: Identifies stations that are safe but inaccessible.",
        "Real-time Logic: Integrated into the Dashboard's 'What-If' simulator."
    ])

    # 6. MONTE CARLO STRESS TESTING
    pdf.add_content_slide("05: Validation via Simulation", [
        "Method: 1,000 randomized Monte Carlo iterations (N=1000).",
        "Variables: Stochastic rainfall distribution vs track thresholds.",
        "Goal: Converge on the 'Systemic Failure Radius' for the MTA grid.",
        "Calibration: Used historical weather data for rainfall distribution curves."
    ], "plots/temp/v3_monte.png")

    # 7. PRELIMINARY FINDINGS: RISK PROFILES
    pdf.add_content_slide("06: Network Risk Distribution", [
        "Intensity Peak: Most track segments trigger at 4.0mm/hr precipitation.",
        "Vulnerability Spread: Infrastructure risk clusters at major junctions.",
        "The 'Weakest Link': Edge failure occurs faster than node inundation.",
        "Finding: 4.0mm/hr is the critical tipping point for system stability."
    ], "plots/temp/v1_dist.png")

    # 8. CRITICAL HUB IDENTIFICATION
    pdf.add_content_slide("07: Single Points of Failure", [
        "Topological Ranking: Identified the Top 5 most critical hubs.",
        "High Priority: New Utrecht Av corridor exhibits a 2.2% failure risk.",
        "Blast Radius: Single hub failures average a 5.2 station isolation radius.",
        "Action: Targeted drainage investments required for red-zone hubs."
    ], "plots/temp/v4_hubs.png")

    # 9. GEOGRAPHIC VULNERABILITY
    pdf.add_content_slide("08: Spatial Station Density", [
        "Density Analysis: Higher station clustering speeds up failure cascades.",
        "South Brooklyn Focus: Prone to total isolation during heavy rainfall.",
        "Manhattan Core: High redundancy but lower intensity resiliency thresholds."
    ], "plots/temp/v2_geo.png")

    # 10. DASHBOARD & DECISION SUPPORT
    pdf.add_content_slide("09: Digital Twin Command Center", [
        "Framework: Streamlit-based UI for real-time situational awareness.",
        "Live KPIs: System Health Index and Orphaned Node counts.",
        "Interactive Rerouting: Implementation of Dijkstra pathfinding logic.",
        "User Focus: Designed for MTA Dispatcher decision support."
    ])

    # 11. CHALLENGES & ROADMAP
    pdf.add_content_slide("10: Project Challenges & Next Steps", [
        "API Latency: Optimizing graph traversal for live data ingestion.",
        "Refinement: Dynamic thresholding based on real-time station elevation.",
        "Deployment: Transitioning to Streamlit Community Cloud hosting.",
        "Collaboration: Finalizing UI hand-off for teammate integration."
    ])

    pdf.output("MTA_Full_10Page_Draft_Deck.pdf")
    print("✅ SUCCESS: 10-Page Slide Deck generated: MTA_Full_10Page_Draft_Deck.pdf")

if __name__ == "__main__":
    generate_10_page_deck()