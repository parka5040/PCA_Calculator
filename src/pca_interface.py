from pandas import DataFrame
from .pca_calc import PCACalculator

class PCAInterface:
    def __init__(self):
        self.pca_calculator = PCACalculator()
        self.df = None
        self.selected_columns = None
        self.label_column = None
        self.pca_results = None

    def load_data(self, df, selected_columns, label_column=None):
        self.df = df
        self.selected_columns = selected_columns
        self.label_column = label_column

    def run_pca(self, n_components=2):
        if self.df is None or not self.selected_columns:
            raise ValueError("Data and selected columns must be set before running PCA")

        X = self.df[self.selected_columns].values
        self.pca_results = self.pca_calculator.fit_transform(X, n_components)

        results = {
            'pca_components': self.pca_results,
            'explained_variance_ratio': self.pca_calculator.get_explained_variance_ratio(),
            'n_components': self.pca_calculator.get_n_components()
        }

        if self.label_column:
            results['labels'] = self.df[self.label_column].values

        return results


    def get_pca_dataframe(self):
        if self.pca_results is None:
            raise ValueError("PCA has not been run yet")

        pca_df = DataFrame(
            self.pca_results,
            columns=[f"PC{i+1}" for i in range(self.pca_calculator.get_n_components())]
        )

        if self.label_column:
            pca_df['label'] = self.df[self.label_column]

        return pca_df

    def get_loadings(self):
        if self.pca_calculator.pca is None:
            raise ValueError("PCA has not been run yet")

        return DataFrame(
            self.pca_calculator.pca.components_.T,
            columns=[f"PC{i+1}" for i in range(self.pca_calculator.get_n_components())],
            index=self.selected_columns
        )

    def reconstruct_original_data(self):
        if self.pca_results is None:
            raise ValueError("PCA has not been run yet")

        reconstructed = self.pca_calculator.inverse_transform(self.pca_results)
        return DataFrame(reconstructed, columns=self.selected_columns)