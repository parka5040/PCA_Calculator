from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA

class PCACalculator:
    def __init__(self):
        self.pca = None
        self.scaler = None
        self.explained_variance_ratio = None
        self.n_components = None

    def fit_transform(self, X, n_components=None):
        # Standardize the features
        self.scaler = StandardScaler()
        X_scaled = self.scaler.fit_transform(X)

        # Perform PCA
        self.pca = PCA(n_components=n_components)
        X_pca = self.pca.fit_transform(X_scaled)

        # Store results
        self.explained_variance_ratio = self.pca.explained_variance_ratio_
        self.n_components = self.pca.n_components_

        return X_pca

    def get_explained_variance_ratio(self):
        return self.explained_variance_ratio

    def get_n_components(self):
        return self.n_components

    def inverse_transform(self, X_pca):
        # Inverse transform PCA
        X_scaled = self.pca.inverse_transform(X_pca)
        # Inverse transform scaling
        return self.scaler.inverse_transform(X_scaled)