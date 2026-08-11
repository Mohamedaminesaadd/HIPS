def plot_feature_by_condition(df, path):
    order = ["baseline", "stress", "amusement", "meditation"]
    colors = {"baseline": "#4c9be8", "stress": "#e8564c",
              "amusement": "#f0a03c", "meditation": "#5cc98b"}
    feats = [f for f in KEY_FEATURES if f in df.columns]
    fig, axes = plt.subplots(2, (len(feats) + 1) // 2, figsize=(13, 7))
    for ax, feat in zip(axes.ravel(), feats):
        data = [df[df["label_name"] == c][feat].dropna() for c in order]
        bp = ax.boxplot(data, tick_labels=order, patch_artist=True, showfliers=False)
        for patch, c in zip(bp["boxes"], order):
            patch.set_facecolor(colors[c]); patch.set_alpha(0.7)
        ax.set_title(feat, fontsize=11); ax.tick_params(axis="x", rotation=30, labelsize=8)
    for ax in axes.ravel()[len(feats):]:
        ax.axis("off")
    fig.suptitle("Features clés par condition", fontsize=13)
    fig.tight_layout(rect=[0, 0, 1, 0.96]); fig.savefig(path, dpi=110); plt.close(fig)
