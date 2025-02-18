from flask import request
from flask_restful import Resource
import scanpy as sc
import os
import sys
import geardb

def tsne_or_umap_present(ana):
  """Return True if tSNE or UMAP plot was calculated for the given analysis."""
  return ana.tsne['tsne_calculated'] == 1 or ana.tsne['umap_calculated'] == 1


class AvailableDisplayTypes(Resource):
    """Resource for retrieving available display types from given dataset id

    Parameters
    ----------
    user_id: str
      User ID
    dataset_id: str
      Dataset ID
    session_id: str
      Session ID

    Returns
    -------
    dict
        Available display types
    """
    def post(self, dataset_id):
        req = request.get_json()
        user_id = req.get('user_id')
        dataset_id = req.get('dataset_id')
        session_id = req.get('session_id')
        analysis_id = req.get('analysis_id')

        line = False
        scatter = True  # Should always have scatter as an option
        contour = False
        tsne_static = False
        umap_static = False
        pca_static = False
        tsne_umap_pca_dynamic = False
        svg_exists = False


        ds = geardb.Dataset(id=dataset_id, has_h5ad=1)
        h5_path = ds.get_file_path()
        # Determine if SVG exists for the primary dataset.
        (base_path, _) = h5_path.split('/datasets/')
        svg_path = f"{base_path}/datasets_uploaded/{dataset_id}.svg"
        if os.path.exists(svg_path):
          svg_exists = True

        # Have a public dataset or user_saved dataset
        if analysis_id:
            # session_id = request.cookies.get('gear_session_id')
            user = geardb.get_user_from_session_id(session_id)

            ana = geardb.Analysis(id=analysis_id, dataset_id=dataset_id, session_id=session_id, user_id=user.id)
            ana.discover_type()
            adata = sc.read_h5ad(ana.dataset_path())
            if hasattr(adata, 'obsm') and 'X_tsne' in adata.obsm:
                tsne_static = True
                tsne_umap_pca_dynamic = True
            elif hasattr(adata, 'obsm') and 'X_umap' in adata.obsm:
                umap_static = True
                tsne_umap_pca_dynamic = True
            elif hasattr(adata, 'obsm') and 'X_pca' in adata.obsm:
                pca_static = True
                tsne_umap_pca_dynamic = True
        else:
          # Dataset is primary type
          if not os.path.exists(h5_path):
              # Let's not fail if the file isn't there
              return {
                  "success": -1,
                  'message': "No h5 file found for this dataset"
              }
          adata = sc.read_h5ad(h5_path)

        columns = adata.obs.columns.tolist()

        if "replicate" in columns:
          columns.remove('replicate')

        for col in columns:
          # If any of the columns are of numerical type,
          # then we can draw line plots
          if "float" in str(adata.obs[col].dtype) or "int" in str(adata.obs[col].dtype):
            line = True

          # if any columns have tSNE in the name, enable support for that.
          if 'tsne'.lower() in str(col).lower():
              tsne_static = True
              tsne_umap_pca_dynamic = True

          # if any columns have UMAP in the name, enable support for that.
          if 'umap'.lower() in str(col).lower():
              umap_static = True
              tsne_umap_pca_dynamic = True

          # if any columns have PCA in the name, enable support for that.
          if 'pca'.lower() in str(col).lower():
              pca_static = True
              tsne_umap_pca_dynamic = True

          # Carlo wants to be able to plot DimRed columns this way
          if str(col).startswith('DimRed') or str(col).startswith('PC'):
              tsne_static = True
              tsne_umap_pca_dynamic = True

        available_display_types = {
          "scatter": scatter,
          "tsne_static": tsne_static,
          "umap_static": umap_static,
          "pca_static": pca_static,
          "tsne/umap_dynamic": tsne_umap_pca_dynamic,
          # Some single cell datasets might have no columns
          "bar": True if len(columns) else False,
          "violin": True if len(columns) else False,
          "line": True if line or "time_point" in columns else False,
          #"contour":True if len(columns) else False,
          "svg": svg_exists
        }

        return available_display_types, 200
