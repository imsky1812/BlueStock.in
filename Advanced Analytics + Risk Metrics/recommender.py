import os
import sqlite3
import pandas as pd

def print_header(title):
    print("=" * 70)
    print(f" {title.upper()} ".center(70, "="))
    print("=" * 70)

def main():
    # Database path relative to this file
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    db_path = os.path.join(base_dir, "Day 2 - Cleaned data + SQLite DB loaded", "bluestock_mf.db")
    
    if not os.path.exists(db_path):
        print(f"Error: Database not found at {db_path}")
        return
        
    conn = sqlite3.connect(db_path)
    
    print_header("Bluestock Fund Recommender")
    print("Welcome! Please select your risk appetite from the options below:")
    print(" 1. Low (Focus on capital preservation - e.g., Liquid funds)")
    print(" 2. Moderate (Balanced growth with medium volatility - Large/Flexi cap)")
    print(" 3. High (Aggressive growth with high volatility - Mid/Small cap)")
    print("-" * 70)
    
    choice = input("Enter your choice (1/2/3 or Low/Moderate/High): ").strip().lower()
    
    if choice in ['1', 'low']:
        risk_appetite = 'Low'
        grades = ['Low']
    elif choice in ['2', 'moderate']:
        risk_appetite = 'Moderate'
        grades = ['Moderate', 'Moderately High']
    elif choice in ['3', 'high']:
        risk_appetite = 'High'
        grades = ['High', 'Very High']
    else:
        print("Invalid choice. Exiting recommender.")
        conn.close()
        return
        
    # Query performance scorecard data
    query = f"""
    SELECT 
        amfi_code, 
        scheme_name, 
        fund_house, 
        category, 
        risk_grade, 
        sharpe_ratio,
        return_3yr_pct,
        aum_crore
    FROM fact_performance
    WHERE risk_grade IN ({','.join(['?' for _ in grades])})
    ORDER BY sharpe_ratio DESC
    LIMIT 3;
    """
    
    df = pd.read_sql_query(query, conn, params=grades)
    
    print()
    print_header(f"Top 3 Recommendations for {risk_appetite} Risk Appetite")
    
    if df.empty:
        print("No matching funds found in the database.")
    else:
        # Print ASCII table
        headers = ["Scheme Name", "Category", "Risk Grade", "Sharpe Ratio", "3-Yr Return (%)", "AUM (Cr)"]
        col_widths = [35, 12, 12, 12, 15, 10]
        
        # Header row
        header_str = " | ".join(f"{h:<{w}}" for h, w in zip(headers, col_widths))
        print(header_str)
        print("-" * len(header_str))
        
        for _, row in df.iterrows():
            name = row['scheme_name']
            if len(name) > 35:
                name = name[:32] + "..."
            
            row_str = (
                f"{name:<35} | "
                f"{row['category']:<12} | "
                f"{row['risk_grade']:<12} | "
                f"{row['sharpe_ratio']:<12.2f} | "
                f"{row['return_3yr_pct']:<15.2f} | "
                f"{row['aum_crore']:<10.1f}"
            )
            print(row_str)
        print("-" * len(header_str))
        print("\nNote: Recommendations are ranked by historical Sharpe Ratio.")
        print("Higher Sharpe Ratio represents better risk-adjusted performance.")
        
    conn.close()

if __name__ == '__main__':
    main()
