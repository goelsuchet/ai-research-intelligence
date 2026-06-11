import pandas as pd
import numpy as np

class QuantInsightEngine:
    def __init__(self):
        """
        Initializes the engine.
        """
        pass

    def _segment_metric(self, df, metric_col):
        segments = {}
        for cat in ['age_group', 'city_tier', 'gender', 'segment', 'variant']:
            if cat in df.columns:
                grouped = df.groupby(cat)[metric_col].mean().dropna().round(2).to_dict()
                if grouped:
                    segments[cat] = grouped
        return segments

    def load_data(self, file_path_or_buffer):
        """Loads CSV or Excel data into a Pandas DataFrame."""
        try:
            if isinstance(file_path_or_buffer, str) and file_path_or_buffer.endswith('.xlsx'):
                return pd.read_excel(file_path_or_buffer)
            else:
                return pd.read_csv(file_path_or_buffer)
        except Exception:
            return None

    @staticmethod
    def reach_at_price(df, price):
        """Pure recompute for Goal 1 interactive what-if"""
        if 'willingness_to_pay_inr' not in df.columns:
            return 0.0
        points = df['willingness_to_pay_inr'].dropna()
        if points.empty:
            return 0.0
        return (points >= price).mean() * 100.0

    @staticmethod
    def rice_at(reach, impact, conf, effort):
        """Pure recompute for Goal 6 interactive what-if"""
        try:
            reach, impact, conf, effort = float(reach), float(impact), float(conf), float(effort)
            if effort <= 0: return 0.0
            return (reach * impact * (conf / 100.0)) / effort
        except Exception:
            return 0.0

    # =========================================================================
    # 🧪 GOAL 1: LAUNCH RESEARCH
    # =========================================================================
    def run_goal_1_analysis(self, df, file_path="Unknown", context=None):
        if context is None: context = {}
        trace_dict = {"tool": "run_goal_1_analysis", "source_file": file_path, "columns_used": [], "rows_analyzed": len(df), "computations": {}, "scenarios": {}, "gap": None, "visuals": []}
        report_lines = ["### 🚀 Goal 1: Launch Viability Report", ""]
        
        market_size = len(df)
        report_lines.append(f"**1. Market Attractiveness**\n- **Sample Size:** {market_size} respondents")
        
        if 'current_brand' in df.columns:
            trace_dict["columns_used"].append('current_brand')
            competitor_count = df['current_brand'].nunique()
            top_brands = df['current_brand'].value_counts().head(3).to_dict()
            density = "High" if competitor_count > 5 else "Low"
            trace_dict["computations"]["competitor_count"] = competitor_count
            trace_dict["computations"]["top_brands"] = top_brands
            report_lines.append(f"\n**2. Competitive Landscape**\n- **Density:** {density} ({competitor_count} active brands)\n- **Top Leaders:** {', '.join([f'{k} ({v})' for k,v in top_brands.items()])}")
            
            # Visual: Competitor Share
            trace_dict["visuals"].append({
                "type": "bar",
                "title": "Top Competitor Share",
                "x": list(top_brands.keys()),
                "y": list(top_brands.values()),
                "x_label": "Brand",
                "y_label": "Mentions"
            })
        else:
            report_lines.append(f"\n**2. Competitive Landscape**\n- ⚠️ Data gap identified: `current_brand` column missing.")
            
        if 'willingness_to_pay_inr' in df.columns:
            trace_dict["columns_used"].append('willingness_to_pay_inr')
            price_points = df['willingness_to_pay_inr'].dropna()
            
            p25 = np.percentile(price_points, 25)
            median = np.median(price_points)
            p75 = np.percentile(price_points, 75)
            p95 = np.percentile(price_points, 95)
            avg_wtp = np.mean(price_points)
            
            trace_dict["computations"]["wtp_stats"] = {"mean": avg_wtp, "p25": p25, "median": median, "p75": p75, "p95": p95}
            
            # Segmentation
            segments = self._segment_metric(df, 'willingness_to_pay_inr')
            if segments:
                trace_dict["computations"]["wtp_segments"] = segments
                report_lines.append("- **Segments:**")
                for cat, group in segments.items():
                    top_seg = max(group, key=group.get)
                    report_lines.append(f"  - Highest {cat}: {top_seg} (₹{group[top_seg]:.2f})")
            
            # Scenarios
            sweep = np.linspace(p25, p95, num=5)
            reach_curve = {f"INR_{int(p)}": round((price_points >= p).mean() * 100, 1) for p in sweep}
            trace_dict["scenarios"]["price_reach_curve_pct"] = reach_curve
            
            # Visuals: WTP Histogram and Reach Curve
            # Histogram bins (simplified)
            hist_y, hist_x = np.histogram(price_points, bins=10)
            trace_dict["visuals"].append({
                "type": "hist",
                "title": "Willingness to Pay Distribution",
                "x": hist_x[:-1].tolist(),
                "y": hist_y.tolist(),
                "x_label": "Price (₹)",
                "y_label": "Count"
            })
            
            trace_dict["visuals"].append({
                "type": "line",
                "title": "Price vs Market Reach",
                "x": sweep.tolist(),
                "y": list(reach_curve.values()),
                "x_label": "Price Point (₹)",
                "y_label": "Reach %"
            })
            
            report_lines.append(f"\n**3. Pricing Feasibility**\n- **Median WTP:** ₹{median:.2f}\n- **Viable Band (p25-p75):** ₹{p25:.2f} - ₹{p75:.2f}")
            
            # Gap Analysis
            target_price = context.get("price_target")
            if target_price:
                reachable_pct = (price_points >= target_price).mean() * 100
                gap_msg = f"Your target price of ₹{target_price} reaches {reachable_pct:.1f}% of the surveyed market."
                if target_price > p95:
                    gap_msg += f" This is above the p95 WTP (₹{p95:.2f}). You are targeting the extreme premium niche."
                elif target_price < p25:
                    gap_msg += f" This is below the p25 WTP (₹{p25:.2f}). You are pricing very competitively."
                
                trace_dict["gap"] = gap_msg
                report_lines.append(f"- **Contextual Gap Analysis:** {gap_msg}")
        else:
            report_lines.append(f"\n**3. Pricing Feasibility**\n- ⚠️ Data gap identified: `willingness_to_pay_inr` column missing.")
            
        return "\n".join(report_lines), trace_dict

    # =========================================================================
    # 📉 GOAL 2: PERFORMANCE DIAGNOSIS
    # =========================================================================
    def run_goal_2_analysis(self, df, file_path="Unknown", context=None):
        if context is None: context = {}
        trace_dict = {"tool": "run_goal_2_analysis", "source_file": file_path, "columns_used": [], "rows_analyzed": len(df), "computations": {}, "scenarios": {}, "gap": None, "visuals": []}
        report_lines = ["### 📉 Goal 2: Performance Diagnosis\n\n**1. KPI Health Check**"]
        
        for col in ['acquisition_cost', 'time_to_value_seconds', 'retention_d30']:
            if col in df.columns:
                trace_dict["columns_used"].append(col)
                if df[col].dtype.kind in 'bifc':
                    # Numeric column: get percentiles
                    vals = df[col].dropna()
                    if not vals.empty:
                        p25, p50, p75 = np.percentile(vals, [25, 50, 75])
                        mean_val = vals.mean()
                        trace_dict["computations"][col] = {"mean": mean_val, "p25": p25, "median": p50, "p75": p75}
                        report_lines.append(f"- **{col}:** Mean: {mean_val:.2f} | Median: {p50:.2f} | P75: {p75:.2f}")
                        
                        # Segmentation
                        segments = self._segment_metric(df, col)
                        if segments:
                            trace_dict["computations"][f"{col}_segments"] = segments
                    else:
                        report_lines.append(f"- ⚠️ Data gap identified: `{col}` has no valid numbers.")
                else:
                    # Categorical / boolean
                    val = df[col].mode()[0] if not df[col].empty else "Unknown"
                    trace_dict["computations"][col] = val
                    report_lines.append(f"- **{col} (Mode):** {val}")
            else:
                report_lines.append(f"- ⚠️ Data gap identified: `{col}` missing.")
        
        report_lines.append("\n**2. Funnel Analysis**")
        if 'funnel_stage' in df.columns:
            trace_dict["columns_used"].append('funnel_stage')
            funnel_order = ["Landing", "Signup", "Onboarding", "Activation", "Paid"]
            existing_stages = [s for s in funnel_order if s in df['funnel_stage'].unique()]
            if not existing_stages:
                existing_stages = df['funnel_stage'].unique().tolist()
                
            counts = df['funnel_stage'].value_counts().reindex(existing_stages).fillna(0)
            if len(counts) > 1:
                drops = counts.diff().abs()
                bottleneck = drops.idxmax()
                
                # Scenarios: Funnel Drop Table
                total_start = counts.iloc[0] if counts.iloc[0] > 0 else 1
                funnel_pct = (counts / total_start * 100).round(1).to_dict()
                trace_dict["scenarios"]["funnel_survival_pct"] = funnel_pct
                
                # Visual: Funnel
                trace_dict["visuals"].append({
                    "type": "funnel",
                    "title": "Funnel Drop-Off",
                    "x": list(funnel_pct.values()),
                    "y": list(funnel_pct.keys()),
                    "x_label": "Survival %",
                    "y_label": "Stage"
                })
            else:
                bottleneck = counts.index[0] if not counts.empty else "N/A"
            trace_dict["computations"]["bottleneck"] = bottleneck
            report_lines.append(f"- **Primary Bottleneck:** {bottleneck}")
        else:
            report_lines.append("- ⚠️ Data gap identified: `funnel_stage` missing.")

        report_lines.append("\n**3. Churn Diagnosis**")
        if 'churn_reason' in df.columns:
            trace_dict["columns_used"].append('churn_reason')
            churn_counts = df['churn_reason'].value_counts()
            total_churn = churn_counts.sum()
            top_churn = churn_counts.head(3)
            
            churn_reasons = []
            for reason, count in top_churn.items():
                pct = (count / total_churn) * 100
                churn_reasons.append(f"{reason} ({pct:.1f}%)")
            
            trace_dict["computations"]["churn_reasons"] = top_churn.to_dict()
            report_lines.append(f"- **Top Reasons:** {', '.join(churn_reasons)}")
            
            # Gap Analysis: Check if the user's hypothesized pain point is a top reason
            hypothesis = context.get("notes", "").lower()
            if hypothesis and "churn" in hypothesis:
                # If they mention a specific churn reason, see if it's in the top 3
                found_match = False
                for reason in top_churn.index:
                    if str(reason).lower() in hypothesis:
                        trace_dict["gap"] = f"Your hypothesized churn reason ('{reason}') aligns with the data. It is a top reason."
                        found_match = True
                        break
                if not found_match:
                    trace_dict["gap"] = "Your hypothesized churn reason does not appear in the top 3 reasons."
                report_lines.append(f"- **Contextual Gap Analysis:** {trace_dict['gap']}")
        else:
            report_lines.append("- ⚠️ Data gap identified: `churn_reason` missing.")

        return "\n".join(report_lines), trace_dict

    # =========================================================================
    # 🎨 GOAL 3: UX & JOURNEY DIAGNOSIS
    # =========================================================================
    def run_goal_3_analysis(self, df, file_path="Unknown", context=None):
        if context is None: context = {}
        trace_dict = {"tool": "run_goal_3_analysis", "source_file": file_path, "columns_used": [], "rows_analyzed": len(df), "computations": {}, "scenarios": {}, "gap": None, "visuals": []}
        report_lines = ["### 🎨 Goal 3: UX & Journey Diagnosis\n\n**1. Cognitive Load Analysis**"]
        
        if 'effort_score' in df.columns:
            efforts = df['effort_score'].dropna()
            avg_effort = round(efforts.mean(), 2)
            p25, median, p75 = np.percentile(efforts, [25, 50, 75])
            trace_dict["computations"]["effort_score"] = {"mean": avg_effort, "p25": p25, "median": median, "p75": p75}
            report_lines.append(f"- **Average Effort Score:** {avg_effort} (Scale 1-10)\n- **Effort Spread:** Median {median:.1f} (P25: {p25:.1f}, P75: {p75:.1f})")
            
            # Segmentation
            segments = self._segment_metric(df, 'effort_score')
            if segments:
                trace_dict["computations"]["effort_segments"] = segments
            
            # Scenarios: Effort distribution if stage available
            if 'funnel_stage' in df.columns:
                stage_effort = df.groupby('funnel_stage')['effort_score'].mean().round(2).to_dict()
                trace_dict["scenarios"]["effort_by_stage"] = stage_effort
                report_lines.append(f"- **Effort by Stage:** {', '.join([f'{k}: {v}' for k,v in stage_effort.items()])}")
                
                # Visual: Effort by stage
                trace_dict["visuals"].append({
                    "type": "bar",
                    "title": "Effort Score by Stage",
                    "x": list(stage_effort.keys()),
                    "y": list(stage_effort.values()),
                    "x_label": "Stage",
                    "y_label": "Effort (1-10)"
                })
        else:
            report_lines.append("- ⚠️ Data gap identified: `effort_score` missing.")
            
        report_lines.append("\n**2. Friction Taxonomy**")
        if 'friction_type' in df.columns:
            frictions = df['friction_type'].value_counts()
            top_friction = frictions.head(3).to_dict()
            friction_points = frictions.index[0] if not frictions.empty else "Unknown"
            trace_dict["computations"]["friction_points"] = friction_points
            trace_dict["computations"]["top_frictions"] = top_friction
            report_lines.append(f"- **Dominant Friction:** {friction_points}\n- **Top Issues:** {', '.join([f'{k} ({v})' for k,v in top_friction.items()])}")
            
            # Gap Analysis
            hypothesis = context.get("notes", "").lower()
            if hypothesis and "friction" in hypothesis:
                found_match = False
                for f in top_friction.keys():
                    if str(f).lower() in hypothesis:
                        trace_dict["gap"] = f"Your hypothesized friction ('{f}') is indeed a top issue."
                        found_match = True
                        break
                if not found_match:
                    trace_dict["gap"] = "Your hypothesized friction does not appear in the top 3 reported issues."
                report_lines.append(f"- **Contextual Gap Analysis:** {trace_dict['gap']}")
        else:
            report_lines.append("- ⚠️ Data gap identified: `friction_type` missing.")

        return "\n".join(report_lines), trace_dict

    # =========================================================================
    # 🔄 GOAL 4: RETENTION & LOYALTY
    # =========================================================================
    def run_goal_4_analysis(self, df, file_path="Unknown", context=None):
        if context is None: context = {}
        trace_dict = {"tool": "run_goal_4_analysis", "source_file": file_path, "columns_used": [], "rows_analyzed": len(df), "computations": {}, "scenarios": {}, "gap": None, "visuals": []}
        report_lines = ["### 🔄 Goal 4: Retention & Loyalty Intelligence\n\n**1. Retention Health**"]
        
        if 'retention_d30' in df.columns:
            trace_dict["columns_used"].append('retention_d30')
            d30_rate_val = df['retention_d30'].mean() * 100
            d30_rate = f"{d30_rate_val:.1f}%"
            trace_dict["computations"]["retention_rate"] = df['retention_d30'].mean()
            report_lines.append(f"- **D30 Retention:** {d30_rate}")
            
            trace_dict["scenarios"]["retention_decay"] = {
                "Day_1": 100.0,
                "Day_7": min(round(d30_rate_val * 1.5, 1), 100.0),
                "Day_14": min(round(d30_rate_val * 1.2, 1), 100.0),
                "Day_30": round(d30_rate_val, 1),
            }
            
            # Visual: Retention Decay
            decay = trace_dict["scenarios"]["retention_decay"]
            trace_dict["visuals"].append({
                "type": "line",
                "title": "Retention Decay Curve",
                "x": list(decay.keys()),
                "y": list(decay.values()),
                "x_label": "Time",
                "y_label": "Retention %"
            })
        elif 'satisfaction_score' in df.columns:
            trace_dict["columns_used"].append('satisfaction_score')
            proxy_rate = (df['satisfaction_score'] >= 8).mean()
            trace_dict["computations"]["retention_proxy"] = proxy_rate
            report_lines.append(f"- **Derived Intent to Repurchase:** {proxy_rate * 100:.1f}% (Proxy from Satisfaction)")
        else:
            report_lines.append("- ⚠️ Data gap identified: `retention_d30` missing.")
            
        report_lines.append("\n**2. Habit Formation**")
        if 'login_frequency' in df.columns:
            trace_dict["columns_used"].append('login_frequency')
            freqs = df['login_frequency'].dropna()
            if not freqs.empty:
                freq_mean = freqs.mean()
                p25, median, p75 = np.percentile(freqs, [25, 50, 75])
                habit_strength = "Strong" if freq_mean > 3 else "Moderate"
                trace_dict["computations"]["login_frequency"] = {"mean": freq_mean, "p25": p25, "median": median, "p75": p75}
                report_lines.append(f"- **Signal Strength:** {habit_strength} (Mean: {freq_mean:.1f}, Median: {median:.1f})")
                
                # Segmentation
                segments = self._segment_metric(df, 'login_frequency')
                if segments:
                    trace_dict["computations"]["login_segments"] = segments
                
                # Gap Analysis
                hypothesis = context.get("notes", "").lower()
                if "daily" in hypothesis or "high frequency" in hypothesis:
                    if median >= 5:
                        trace_dict["gap"] = "Your hypothesis of 'daily/high frequency' is supported by a median login rate of >= 5."
                    else:
                        trace_dict["gap"] = f"Your hypothesis of 'high frequency' contrasts with actual median frequency of {median:.1f}."
                    report_lines.append(f"- **Contextual Gap Analysis:** {trace_dict['gap']}")
            else:
                report_lines.append("- ⚠️ Data gap identified: `login_frequency` contains no valid numbers.")
        else:
            report_lines.append("- ⚠️ Data gap identified: `login_frequency` missing.")

        return "\n".join(report_lines), trace_dict

    # =========================================================================
    # 🧪 GOAL 5: HYPOTHESIS VALIDATION
    # =========================================================================
    def run_goal_5_analysis(self, df, file_path="Unknown", context=None):
        if context is None: context = {}
        trace_dict = {"tool": "run_goal_5_analysis", "source_file": file_path, "columns_used": [], "rows_analyzed": len(df), "computations": {}, "scenarios": {}, "gap": None, "visuals": []}
        report_lines = [f"### ⚖️ Goal 5: A/B Test Diagnosis\n\n**1. Primary Metric Shift**\n- **Hypotheses Reviewed:** {len(df)}", "\n**2. Evidence Classification**"]
        
        if 'p_value' in df.columns:
            trace_dict["columns_used"].append('p_value')
            sig_level = "Statistically Significant" if df['p_value'].min() < 0.05 else "Inconclusive"
            trace_dict["computations"]["min_p_value"] = df['p_value'].min()
            report_lines.append(f"- **Signal Strength:** {sig_level}")
        else:
            report_lines.append("- ⚠️ Data gap identified: `p_value` missing.")
            
        if 'variant' in df.columns and 'conversion_rate' in df.columns:
            trace_dict["columns_used"].extend(['variant', 'conversion_rate'])
            variant_conv = df.groupby('variant')['conversion_rate'].mean().to_dict()
            trace_dict["computations"]["variant_conversion"] = variant_conv
            
            # Segmentation
            segments = self._segment_metric(df, 'conversion_rate')
            if segments:
                trace_dict["computations"]["conversion_segments"] = segments
                
            report_lines.append("\n**3. Variant Performance**")
            for var, conv in variant_conv.items():
                report_lines.append(f"- **{var}:** {conv*100:.1f}%")
                
            # Visual: Variant Conversion
            trace_dict["visuals"].append({
                "type": "bar",
                "title": "Conversion Rate by Variant",
                "x": list(variant_conv.keys()),
                "y": [v * 100 for v in variant_conv.values()],
                "x_label": "Variant",
                "y_label": "Conversion %"
            })
                
            winning_variant = max(variant_conv, key=variant_conv.get)
            trace_dict["computations"]["winning_variant"] = winning_variant
            
            # Scenarios: Lift
            baseline_conv = variant_conv.get("control", variant_conv.get(list(variant_conv.keys())[0]))
            winner_conv = variant_conv[winning_variant]
            if baseline_conv and baseline_conv > 0:
                relative_lift = ((winner_conv - baseline_conv) / baseline_conv) * 100
                trace_dict["scenarios"]["lift"] = {"winner": winning_variant, "relative_lift_pct": round(relative_lift, 1)}
                report_lines.append(f"- **Relative Lift:** +{relative_lift:.1f}% (for {winning_variant})")
                
            # Gap Analysis
            hypothesis = context.get("notes", "").lower()
            if hypothesis:
                if str(winning_variant).lower() in hypothesis:
                    trace_dict["gap"] = f"Your hypothesized variant ('{winning_variant}') is indeed the winner."
                else:
                    trace_dict["gap"] = f"Your hypothesis does not match the winning variant ('{winning_variant}')."
                report_lines.append(f"- **Contextual Gap Analysis:** {trace_dict['gap']}")

        return "\n".join(report_lines), trace_dict

    # =========================================================================
    # 📋 GOAL 6: PRIORITIZATION & ROADMAP
    # =========================================================================
    def run_goal_6_analysis(self, df, file_path="Unknown", context=None):
        if context is None: context = {}
        trace_dict = {"tool": "run_goal_6_analysis", "source_file": file_path, "columns_used": [], "rows_analyzed": len(df), "computations": {}, "scenarios": {}, "gap": None, "visuals": []}
        report_lines = ["### 🗺️ Goal 6: Feature Roadmap Validation\n\n**1. Backlog Sizing**"]
        
        if 'impact_score' in df.columns and 'effort_score' in df.columns:
            trace_dict["columns_used"].extend(['impact_score', 'effort_score'])
            df_local = df.copy()
            impact = df_local['impact_score']
            effort = df_local['effort_score']
            confidence = df_local['confidence_score'] if 'confidence_score' in df_local.columns else 1.0
            reach = df_local['reach'] if 'reach' in df_local.columns else 1.0
            if 'confidence_score' in df_local.columns:
                trace_dict["columns_used"].append('confidence_score')
            if 'reach' in df_local.columns:
                trace_dict["columns_used"].append('reach')
            
            df_local['rice_score'] = (reach * impact * confidence) / effort.replace(0, 0.1)
            
            # Get Top 5 for scenarios
            df_sorted = df_local.sort_values('rice_score', ascending=False)
            top_5 = df_sorted.head(5)
            
            scenario_table = {}
            for idx, row in top_5.iterrows():
                fname = row.get('feature_name', f'Item {idx}')
                scenario_table[fname] = round(row['rice_score'], 2)
            trace_dict["scenarios"]["top_features_rice"] = scenario_table
            
            best_row = top_5.iloc[0]
            top_item = best_row.get('feature_name', "Item #1")
            rice_score = round(best_row['rice_score'], 2)
            trace_dict["computations"]["top_item"] = top_item
            trace_dict["computations"]["rice_score"] = rice_score
            report_lines.append(f"- **#1 Priority:** {top_item}\n- **Score:** {rice_score}")
            report_lines.append(f"- **Runner Ups:** {', '.join(list(scenario_table.keys())[1:3])}")
            
            # Segmentation
            segments = self._segment_metric(df_local, 'rice_score')
            if segments:
                trace_dict["computations"]["rice_segments"] = segments
            
            # Visual: Impact vs Effort (scatter)
            trace_dict["visuals"].append({
                "type": "scatter",
                "title": "RICE: Impact vs Effort",
                "x": df_local['effort_score'].tolist(),
                "y": df_local['impact_score'].tolist(),
                "x_label": "Effort Score",
                "y_label": "Impact Score",
                "text": df_local.get('feature_name', pd.Series([f"Item {i+1}" for i in range(len(df_local))])).tolist()
            })
            
            # Gap Analysis
            hypothesis = context.get("notes", "").lower()
            if hypothesis:
                found_rank = None
                for i, fname in enumerate(scenario_table.keys()):
                    if str(fname).lower() in hypothesis:
                        found_rank = i + 1
                        break
                if found_rank:
                    trace_dict["gap"] = f"Your hypothesized feature is ranked #{found_rank} in the RICE priority list."
                else:
                    trace_dict["gap"] = "Your hypothesized feature did not make the top 5."
                report_lines.append(f"- **Contextual Gap Analysis:** {trace_dict['gap']}")
        else:
            report_lines.append("- ⚠️ Data gap identified: `impact_score` or `effort_score` missing.")

        return "\n".join(report_lines), trace_dict

    # =========================================================================
    # 📢 GOAL 7: EXECUTIVE SUMMARY
    # =========================================================================
    def run_goal_7_analysis(self, df, file_path="Unknown", context=None):
        if context is None: context = {}
        trace_dict = {"tool": "run_goal_7_analysis", "source_file": file_path, "columns_used": list(df.columns), "rows_analyzed": len(df), "computations": {}, "scenarios": {}, "gap": None, "visuals": []}
        
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        stats = []
        health_scores = {}
        for col in numeric_cols:
            mean_val = df[col].mean()
            std_val = df[col].std()
            stats.append(f"- **{col}**: Mean {mean_val:.2f}, Std {std_val:.2f}")
            trace_dict["computations"][f"{col}_mean"] = mean_val
            
            # Simple scenario: normalize the mean as a 1-100 score relative to max
            max_val = df[col].max()
            if max_val and max_val > 0:
                health_scores[col] = round((mean_val / max_val) * 100, 1)
                
        trace_dict["scenarios"]["health_scores"] = health_scores
        
        if health_scores:
            trace_dict["visuals"].append({
                "type": "bar",
                "title": "Normalized Health Scores",
                "x": list(health_scores.keys()),
                "y": list(health_scores.values()),
                "x_label": "Metric",
                "y_label": "Score (0-100)"
            })
        
        report_lines = [
            f"### 📢 Goal 7: Executive Strategy Brief",
            f"**1. The Bottom Line**",
            f"- **Dataset:** Analyzed {len(df)} data points.",
            f"\n**2. Aggregate Statistics**"
        ] + stats
        
        return "\n".join(report_lines), trace_dict