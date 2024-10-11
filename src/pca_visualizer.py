from numpy import unique, linspace, cumsum
from pandas import api
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PyQt6.QtWidgets import QVBoxLayout, QWidget
from sklearn.preprocessing import LabelEncoder

class PCAVisualizer:
    def __init__(self, pca_interface):
        self.pca_interface = pca_interface
        self.label_encoder = LabelEncoder()

    def _prepare_labels(self, labels):
        if labels is None:
            return None, None
        
        if api.types.is_numeric_dtype(labels):
            return labels, labels
        else:
            encoded_labels = self.label_encoder.fit_transform(labels)
            return encoded_labels, labels

    def plot_2d(self, ax):
        pca_df = self.pca_interface.get_pca_dataframe()
        
        if 'label' in pca_df.columns:
            encoded_labels, original_labels = self._prepare_labels(pca_df['label'])
            scatter = ax.scatter(pca_df['PC1'], pca_df['PC2'], c=encoded_labels, cmap='viridis')
            
            if original_labels is not None and not api.types.is_numeric_dtype(original_labels):
                unique_labels = unique(original_labels)
                legend_elements = [plt.Line2D([0], [0], marker='o', color='w', 
                                              markerfacecolor=plt.cm.viridis(self.label_encoder.transform([label])[0] / len(unique_labels)), 
                                              markersize=10, label=label) for label in unique_labels]
                ax.legend(handles=legend_elements, title='Labels', loc='center left', bbox_to_anchor=(1, 0.5))
            else:
                plt.colorbar(scatter, ax=ax, label='Label')
        else:
            ax.scatter(pca_df['PC1'], pca_df['PC2'])
        
        ax.set_xlabel('PC1')
        ax.set_ylabel('PC2')
        ax.set_title('Two Dimensional PCA')

    def plot_3d(self, ax):
        pca_df = self.pca_interface.get_pca_dataframe()
        
        if 'label' in pca_df.columns:
            encoded_labels, original_labels = self._prepare_labels(pca_df['label'])
            
            if original_labels is not None and not api.types.is_numeric_dtype(original_labels):
                unique_labels = unique(original_labels)
                colors = plt.cm.viridis(linspace(0, 1, len(unique_labels)))
                
                for label, color in zip(unique_labels, colors):
                    mask = original_labels == label
                    ax.scatter(pca_df.loc[mask, 'PC1'], 
                               pca_df.loc[mask, 'PC2'], 
                               pca_df.loc[mask, 'PC3'], 
                               c=[color], 
                               label=label)
                
                ax.legend(title='Labels', loc='center left', bbox_to_anchor=(1.1, 0.5))
            else:
                scatter = ax.scatter(pca_df['PC1'], pca_df['PC2'], pca_df['PC3'], 
                                     c=encoded_labels, cmap='viridis')
                plt.colorbar(scatter, ax=ax, label='Label')
        else:
            ax.scatter(pca_df['PC1'], pca_df['PC2'], pca_df['PC3'])
        
        ax.set_xlabel('PC1')
        ax.set_ylabel('PC2')
        ax.set_zlabel('PC3')
        ax.set_title('Three Dimensional PCA')

    def get_explained_variance_text(self):
        explained_variance_ratio = self.pca_interface.pca_calculator.get_explained_variance_ratio()
        cumulative_variance_ratio = cumsum(explained_variance_ratio)
        
        text = "Explained Variance Ratio:\n"
        for i, (var, cum_var) in enumerate(zip(explained_variance_ratio, cumulative_variance_ratio), 1):
            text += f"PC{i}: {var:.4f} (Cumulative: {cum_var:.4f})\n"
        
        return text

    def visualize(self, is_3d=False):
        n_components = self.pca_interface.pca_calculator.get_n_components()
        
        fig = plt.figure(figsize=(10, 8))
        if is_3d and n_components >= 3:
            ax = fig.add_subplot(111, projection='3d')
            self.plot_3d(ax)
        else:
            ax = fig.add_subplot(111)
            self.plot_2d(ax)
        
        plt.tight_layout()
        return fig, self.get_explained_variance_text()