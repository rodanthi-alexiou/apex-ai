import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np

def generate_cost_projection_chart(
    months: list,
    costs: list,
    output_path: str = "03-des-cost-projection.png",
    budget_cap: float = None,
    growth_assumption: str = None,
) -> None:
    """Render a bar + trend-line chart for 6-month cost projections."""
    fig, ax = plt.subplots(figsize=(10, 5))
    fig.patch.set_facecolor("#F8F9FA")
    ax.set_facecolor("#F8F9FA")

    x = np.arange(len(months))
    bar_color = "#0078D4"

    bars = ax.bar(x, costs, color=bar_color, alpha=0.85,
                  edgecolor="white", linewidth=1.5, width=0.55)

    for bar, cost in zip(bars, costs):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + max(costs) * 0.015,
                f"${cost:,.0f}", ha="center", va="bottom",
                fontsize=9, fontweight="bold", color="#333")

    z   = np.polyfit(x, costs, 1)
    p   = np.poly1d(z)
    x_smooth = np.linspace(0, len(months) - 1, 200)
    ax.plot(x_smooth, p(x_smooth), color="#FF8C00", linewidth=2,
            linestyle="--", alpha=0.8, label="Trend")

    if budget_cap is not None:
        ax.axhline(budget_cap, color="#DC3545", linewidth=1.5,
                   linestyle=":", alpha=0.8, label=f"Budget cap  ${budget_cap:,.0f}")

    ax.set_xticks(x)
    ax.set_xticklabels(months, fontsize=10, color="#333")
    ax.set_ylabel("Monthly Cost (USD)", fontsize=10, color="#555")

    title = "6-Month Cost Projection - Moda Iberica Assistant"
    ax.set_title(title, fontsize=13, fontweight="bold",
                 color="#1A1A2E", pad=14 if not growth_assumption else 22)
    if growth_assumption:
        ax.text(0.5, 1.02, growth_assumption, transform=ax.transAxes,
                ha="center", fontsize=9, color="#888", style="italic")

    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"${v:,.0f}"))
    ax.tick_params(axis="y", labelsize=9, colors="#666")
    ax.spines[["top", "right"]].set_visible(False)
    ax.spines[["left", "bottom"]].set_color("#DDD")
    ax.grid(axis="y", color="#E0E0E0", linewidth=0.8, alpha=0.7)
    ax.set_ylim(0, max(costs) * 1.25)

    ax.legend(fontsize=9, framealpha=0.9, edgecolor="#CCC")

    plt.tight_layout(pad=1.4)
    plt.savefig(output_path, dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close()
    print(f"Generated: {output_path}")


# Phased growth: MVP (Aug) -> Full (Oct) -> Peak (Nov) -> Optimize (Dec)
# June-July: Dev/test only, Aug: MVP launch, Sep: ramp, Oct: Full, Nov: Black Friday
months = ["Jul 2026", "Aug 2026", "Sep 2026", "Oct 2026", "Nov 2026", "Dec 2026"]
costs  = [4200, 7500, 9800, 13500, 31000, 14000]

generate_cost_projection_chart(
    months, costs,
    output_path="agent-output/moda-iberica-assistant/03-des-cost-projection.png",
    budget_cap=30000,
    growth_assumption="Based on phased rollout: MVP (Aug) -> Full Launch (Oct) -> Black Friday peak (Nov, 3x)",
)
