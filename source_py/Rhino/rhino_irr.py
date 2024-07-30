from __future__ import division
import rhinoinside
rhinoinside.load()

import os
from honeybee_radiance.recipe import Recipe
from honeybee_radiance.results import recipe_result

def annual_irradiance(_model, _wea, _timestep_ = 1, visible_ = False, north_ = 0, grid_filter_ = None, radiance_par_ = "-ab 2 -ad 5000 -lw 2e-05", run_settings_ = None):
    """
    Run an annual irradiance study for a Honeybee model to compute hourly solar
    irradiance for each sensor in a model's sensor grids.
    
    Args:
        _model: A Honeybee Model for which Annual Irradiance will be simulated.
        _wea: A Wea object or path to a .wea or .epw file.
        _timestep_: Integer for the timestep of the input _wea.
        visible_: Boolean to indicate whether to compute visible irradiance.
        north_: Number for the counterclockwise difference between the North and the positive Y-axis in degrees.
        grid_filter_: Text for a grid identifier or pattern to filter the sensor grids.
        radiance_par_: Text for the radiance parameters to be used for ray tracing.
        run_settings_: Settings from the "HB Recipe Settings" component or text string of recipe settings.

    Returns:
        results: Raw result files (.ill) containing matrices of irradiance in W/m2.
    """
    # Create the recipe and set input arguments
    recipe = Recipe('annual-irradiance')
    recipe.input_value_by_name('model', _model)
    recipe.input_value_by_name('wea', _wea)
    recipe.input_value_by_name('timestep', _timestep_)
    recipe.input_value_by_name('output-type', visible_)
    recipe.input_value_by_name('north', north_)
    recipe.input_value_by_name('grid-filter', grid_filter_)
    recipe.input_value_by_name('radiance-parameters', radiance_par_)

    if run_settings_ is not None:
        project_folder = recipe.run(run_settings_, radiance_check=True, silent=False)

    recipe.default_project_folder = os.path.join('C:', 'Users', 'maceo.valente', 'Documents', 'Automatisation', 'TEST_MVA', 'TSAgriPV')
    
    # Load the results
    results = recipe_result(recipe.output_value_by_name('results', project_folder))

    return results