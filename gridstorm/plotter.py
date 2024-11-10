from enum import Enum
import logging
import math
from tqdm import tqdm

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import matplotlib.patches as patches
import matplotlib.animation
import matplotlib.image
from matplotlib.offsetbox import TextArea, DrawingArea, OffsetImage, AnnotationBbox


logger = logging.getLogger(__name__)

colors = mpl.colors.ListedColormap(['#FFFFFF', 'crimson', 'green', 'gold', 'violet', 'lightskyblue', 'orange', 'greenyellow'])
data_colors = {
    "TRAP" : 1,
    "GOAL" : 2,
    "LANDMARK" : 3,
    "ADVBELIEF" : 4,
    "EGOBELIEF" : 5,
    "ADVGOAL" : 6,
    "GOALAREA" : 7
}


class InteractiveLandmarkStatus(Enum):
    CLEARED = 1,
    POSITIVE = 2,
    NEGATIVE = 3


class InteractiveLandmarkBelief(Enum):
    CLEARED = 1,
    KNOWN = 2,
    QUESTIONMARK = 3


class Plotter:
    def __init__(self, program, annotation, model):
        self._program  = program
        self._model = model
        self._state_vals = model.state_valuations
        self._tmp_objects = []
        self._annotation =  annotation
        self._clear()
        self._fig = None
        self._ax = None
        self._ax_res = None
        self._ax_info = None
        self._init_fig()
        self._ego_image = None
        self._title = None

        self._ego_scanned_last_round = False

    def set_title(self, title):
        self._title = title
        self._fig.suptitle(self._title, fontsize=16)

    def _reset(self):
        self._clear()
        self._fig = None
        self._ax = None
        plt.clf()
        self._init_fig()
        self._fig.suptitle(self._title, fontsize=16)

    @property
    def _maxX(self):
        return self._program.get_constant(self._annotation.xmax_constant).definition.evaluate_as_int()

    @property
    def _minX(self):
        # TODO allow to change this value (Currently this breaks in various lcoations if this is not 0).
        return 0

    @property
    def _maxY(self):
        return self._program.get_constant(self._annotation.ymax_constant).definition.evaluate_as_int()

    @property
    def _minY(self):
        # TODO allow to change this value (Currently this breaks in various locations if this is not 0)
        return 0

    @property
    def _targets(self):
        lab = self._model.labeling
        result = []
        if self._annotation.has_static_targets:
            for s in lab.get_states(self._annotation.target_label):
                result.append(self._get_ego_loc(s))
        return result

    @property
    def _landmarks(self):
        lab = self._model.labeling
        result = []
        if self._annotation.has_landmarks:
            for s in lab.get_states(self._annotation.landmark_label):
                result.append(self._get_ego_loc(s))
        return result

    @property
    def _traps(self):
        lab = self._model.labeling
        result = []
        if self._annotation.traps_label:
            for s in lab.get_states(self._annotation.traps_label):
                result.append(self._get_ego_loc(s))
        return result

    @property
    def _adv_goals(self):
        lab = self._model.labeling
        result = []
        if self._annotation.adv_goal_label:
            for s in lab.get_states(self._annotation.adv_goal_label):
                result.append(self._get_adv_loc(s))
        return result

    def load_ego_image(self, path, zoom=0.2):
        img = mpl.image.imread(path)
        #self._ego_image = OffsetImage(img, zoom=zoom)

    def _clear(self):
        self._data = np.zeros((self._maxY - self._minY + 1, self._maxX - self._minX + 1))
        for ob in self._traps:
            self._set_bad(ob[0], ob[1])
        for t in self._targets:
            self._set_goal(t[0], t[1])
        for l in self._landmarks:
            self._set_landmark(l[0], l[1])
        for g in self._adv_goals:
            self._set_adv_goal(g[0], g[1])
        for o in self._tmp_objects:
            o.remove()
        self._tmp_objects = []

    def wipe(self):
        self._init_fig()
        self._clear()

    def _init_fig(self):
        w, h = plt.figaspect(.75)
        self._fig = plt.Figure(figsize=(w, h))
        #self._fig = plt.figure(constrained_layout=True)
        if self._annotation.has_resources:
            reswidth = 2
            widths = [30, reswidth, 4]
            height_ratios = [1]
            spec = self._fig.add_gridspec(ncols=3, nrows=1, width_ratios=widths, height_ratios=height_ratios)
            self._ax = self._fig.add_subplot(spec[0, 0])
            self._ax_res = self._fig.add_subplot(spec[0, 1])
            self._ax_info = self._fig.add_subplot(spec[0, 2])
        else:
            widths = [30,  6]
            height_ratios = [1]
            spec = self._fig.add_gridspec(ncols=2, nrows=1, width_ratios=widths, height_ratios=height_ratios)
            self._ax = self._fig.add_subplot(spec[0, 0])
            self._ax_info = self._fig.add_subplot(spec[0, 1])

        ax = self._ax
        column_labels = list(range(0, self._maxX + 1))
        ax.set_xlim([-0.4, self._maxX+1.4])
        ax.set_ylim([-0.4, self._maxY+1.4])
        row_labels = list(range(0, self._maxY + 1))
        # put the major ticks at the middle of each cell
        ax.set_xticks(np.arange(self._data.shape[0]) + 0.5, minor=False)
        ax.set_yticks(np.arange(self._data.shape[1]) + 0.5, minor=False)

        # want a more natural, table-like display
        ax.invert_yaxis()
        ax.xaxis.tick_top()

        ax.set_xticklabels(row_labels, minor=False)
        ax.set_yticklabels(column_labels, minor=False)
        ax.set_xlabel("x")
        ax.set_ylabel("y")
        ax.set_aspect(1)
        if self._annotation.has_resources:
            ax = self._ax_res
            ax.set_xticklabels(self._annotation.resource_names, minor=False)
        ax = self._ax_info
        ax.set_axis_off()
        self._tmp_objects = []

    def _set_bad(self, xloc, yloc):
        self._data[yloc,xloc] = data_colors["TRAP"]

    def _set_goal(self, xloc, yloc):
        if self._annotation.has_goal_action:
            self._data[yloc, xloc] = data_colors["GOALAREA"]
        else:
            self._data[yloc,xloc] = data_colors["GOAL"]

    def _set_landmark(self, xloc, yloc):
        self._data[yloc,xloc] = data_colors["LANDMARK"]

    def _set_adv_goal(self, xloc, yloc):
        self._data[yloc,xloc] = data_colors["ADVGOAL"]

    def _set_interactive_landmarks(self, xloc, yloc, status, belief, index):
        if status != InteractiveLandmarkStatus.CLEARED:
            if status == InteractiveLandmarkStatus.POSITIVE:
                color = 'darkgreen'
            elif status == InteractiveLandmarkStatus.NEGATIVE:
                color = 'darkred'
            adv = patches.RegularPolygon((xloc + 0.5, yloc + 0.5), 7, 0.35, linewidth=1, edgecolor=color, facecolor=color)
            props = dict(boxstyle='round', facecolor='yellow', alpha=1)
            propsid = dict(boxstyle='round', facecolor='white', alpha=0.7)
            text = "?" if belief == InteractiveLandmarkBelief.QUESTIONMARK else "!"
            self._ax.add_patch(adv)
            txt = self._ax.text(xloc + 0.6, yloc + 0.6, text, fontsize=10,
                                verticalalignment='top', bbox=props)
            self._tmp_objects.append(txt)
            txt = self._ax.text(xloc + 0.3, yloc + 0.3, str(index+1), fontsize=10,
                                verticalalignment='top', bbox=propsid)
            self._tmp_objects.append(txt)

            self._tmp_objects.append(adv)

    def _set_adversary(self, xloc, yloc, adv_direction, radius, i=0):
        if adv_direction is None:
            adv = patches.Rectangle((xloc + 0.25, yloc + 0.25), 0.5, 0.5, linewidth=1, edgecolor='saddlebrown', facecolor='sienna')
        else:

            adv = patches.RegularPolygon((xloc+0.5, yloc+0.5), 3, 0.35, linewidth=1, edgecolor='saddlebrown', facecolor='sienna')
            t2 = mpl.transforms.Affine2D().rotate_around(xloc+0.5, yloc+0.5, np.deg2rad(adv_direction.rotation)) + self._ax.transData
            adv.set_transform(t2)
        self._ax.add_patch(adv)
        self._tmp_objects.append(adv)

        if radius:
            viewarea_xlb = max(0, xloc - radius)
            viewarea_ylb = max(0, yloc - radius)
            viewarea_xub = min(self._maxX, xloc + radius)
            viewarea_yub = min(self._maxY, yloc + radius)
            viewarea = patches.Rectangle((viewarea_xlb, viewarea_ylb), viewarea_xub-viewarea_xlb+1, viewarea_yub-viewarea_ylb+1, linewidth=0.4, edgecolor='r', facecolor='r', alpha=0.1, hatch='x' )
            self._ax.add_patch(viewarea)
            self._tmp_objects.append(viewarea)

        props = dict(boxstyle='round', facecolor='lavender', alpha=0.5)
        if adv_direction is None:
            text = f"x={xloc},y={yloc}"
        else:
            text = f"x={xloc},y={yloc},d={adv_direction}"
        txt = self._ax_info.text(0.05, 0.88-i*0.07, text, transform=self._ax_info.transAxes, fontsize=10,
                      verticalalignment='top', bbox=props)
        self._tmp_objects.append(txt)

    def _set_ego(self, ax, xloc, yloc, radius):
        # Create a Rectangle patch
        if self._ego_image:
            ego = AnnotationBbox(self._ego_image, (xloc+0.5, yloc+0.5))
            ax.add_artist(ego)
        else:
            ego = patches.Rectangle((xloc+0.25, yloc+0.25), 0.5, 0.5, linewidth=1, edgecolor='b', facecolor='b')
            ax.add_patch(ego)

        if radius:
            viewarea_xlb = max(0, xloc - radius)
            viewarea_ylb = max(0, yloc - radius)
            viewarea_xub = min(self._maxX, xloc + radius)
            viewarea_yub = min(self._maxY, yloc + radius)
            viewarea = patches.Rectangle((viewarea_xlb, viewarea_ylb), viewarea_xub-viewarea_xlb+1, viewarea_yub-viewarea_ylb+1, linewidth=7, edgecolor='b', facecolor='b', alpha=0.05, hatch='o' )
            self._ax.add_patch(viewarea)
            self._tmp_objects.append(viewarea)

        self._tmp_objects.append(ego)

        props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)
        text = f"x={xloc},y={yloc}"
        txt = self._ax_info.text(0.05, 0.95, text, transform=self._ax_info.transAxes, fontsize=10,
                verticalalignment='top', bbox=props)
        self._tmp_objects.append(txt)

        # Add the patch to the Axes

    def _set_resources(self, relative_height):
        bar = self._ax_res.bar(0, relative_height * 1, width=1, color='black', bottom=0, align='center', data=None)
        self._tmp_objects.append(bar)

    def _set_ego_alternatives(self, ax, xloc, yloc):
        self._data[yloc,xloc] = data_colors["EGOBELIEF"]

    def _set_adv_alternatives(self, xloc, yloc):
        self._data[yloc,xloc] = data_colors["ADVBELIEF"]

    def _get_int_value(self, state, var):
        return self._state_vals.get_integer_value(state,var)

    def _get_bool_value(self, state, var):
        return self._state_vals.get_boolean_value(state,var)

    def _get_action_string(self, state, action):
        if action is None:
            return None
        return list(self._model.choice_labeling.get_labels_of_choice(self._model.get_choice_index(state, action)))[0]

    def _set_actions(self, state, xloc, yloc, available, allowed, selected):
        acts = self._model.choice_labeling.get_labels()
        maxlen = 0
        for act in acts:
            maxlen = max(maxlen, len(act))

        available_strings = [ list(self._model.choice_labeling.get_labels_of_choice(self._model.get_choice_index(state, act))) for act in available]
        available_strings = [ l[0] if len(l)>0 else None for l in available_strings]
        allowed_strings = [list(self._model.choice_labeling.get_labels_of_choice(self._model.get_choice_index(state, act))) for act in
                             allowed]
        allowed_strings = [l[0] if len(l) > 0 else None for l in allowed_strings]
        if selected is not None:
            selected_string = list(self._model.choice_labeling.get_labels_of_choice(self._model.get_choice_index(state,selected)))[0]
        else:
            selected_string = "--end--"
        logger.debug(available_strings)
        logger.debug(allowed_strings)
        logger.debug(selected_string)
        props_unavailable = dict(boxstyle='round', facecolor='gray', alpha=0.5)
        props_notallowed = dict(boxstyle='round', facecolor='red', alpha=0.5)
        props_notselected = dict(boxstyle='round', facecolor='wheat', alpha=0.5)
        props_selected = dict(boxstyle='round', facecolor='green', alpha=0.5)
        for i,act in enumerate(acts):
            text = act.ljust(maxlen)
            if act not in available_strings:
                props = props_unavailable
            elif act not in allowed_strings:
                props = props_notallowed
            elif act == selected_string:
                props = props_selected
            else:
                props = props_notselected
            txt = self._ax_info.text(0.05, 0.70-0.07*i, text, fontdict={'family': 'monospace'}, transform=self._ax_info.transAxes, fontsize=10,
                       verticalalignment='top', bbox=props)
            self._tmp_objects.append(txt)
            if act not in ["north", "east", "west", "south"]:
                continue
            if act not in available_strings:
                continue
            if act == selected_string:
                fcol = 'green'
                ecol = 'green'
            elif act not in allowed_strings:
                fcol = 'red'
                ecol = 'red'
            else:
                fcol = 'black'
                ecol = 'black'
            if act == "north":
                dx = 0
                dy = -0.6
            if act == "south":
                dx = 0
                dy = 0.6
            if act == "west":
                dx = -0.6
                dy = 0
            if act == "east":
                dx = 0.6
                dy = 0
            arr = self._ax.arrow(xloc+0.5, yloc+0.5, dx, dy, head_width=0.12, ec=ecol, fc=fcol, lw=0.01)
            self._tmp_objects.append(arr)

    def _get_ego_loc(self, state):
        module, var = self._annotation.ego_xvar_identifier
        xvar = self._program.get_module(module).get_integer_variable(var).expression_variable
        module, var = self._annotation.ego_yvar_identifier
        yvar = self._program.get_module(module).get_integer_variable(var).expression_variable

        ego_xloc = self._get_int_value(state, xvar)
        ego_yloc = self._get_int_value(state, yvar)
        return ego_xloc, ego_yloc

    def _get_adv_loc(self, state, index=0):
        module, var = self._annotation.adv_xvar_identifier(index)
        xvar = self._program.get_module(module).get_integer_variable(var).expression_variable
        module, var = self._annotation.adv_yvar_identifier(index)
        yvar = self._program.get_module(module).get_integer_variable(var).expression_variable

        adv_xloc = self._get_int_value(state, xvar)
        adv_yloc = self._get_int_value(state, yvar)
        assert adv_xloc <= self._maxX
        assert adv_yloc <= self._maxY, f"Yloc {adv_yloc} should be on the grid with dimension {self._maxY}"
        return adv_xloc, adv_yloc

    def _get_interactive_landmark_loc(self, index):
        xconst, yconst = self._annotation.interactive_landmark_constants(index)
        x = self._program.get_constant(xconst).definition.evaluate_as_int()
        y = self._program.get_constant(yconst).definition.evaluate_as_int()
        return x,y

    def _get_interactive_landmark_status(self, state, index):
        module, var = self._annotation.interactive_landmark_status_identifier(index)
        status_var = self._program.get_module(module).get_boolean_variable(var).expression_variable
        status_val = self._get_bool_value(state, status_var)
        module, var = self._annotation.interactive_landmark_clearance_identifier(index)

        clearance_var = self._program.get_module(module).get_boolean_variable(var).expression_variable
        clearance_val = self._get_bool_value(state, clearance_var)
        if not clearance_val:
            status = InteractiveLandmarkStatus.POSITIVE if status_val else InteractiveLandmarkStatus.NEGATIVE
        else:
            status = InteractiveLandmarkStatus.CLEARED
        return status

    def _get_adv_direction(self, state, index=0):
        if self._annotation.adv_has_direction:
            module, var = self._annotation.adv_dir_identifier(index)
            dirvar = self._program.get_module(module).get_integer_variable(var).expression_variable
            return self._annotation.adversary_direction_value_to_direction(self._get_int_value(state, dirvar))
        else:
            return None

    def _get_adv_radius(self):
        radconstant = self._annotation.adv_radius_constant
        if radconstant:
            return self._program.get_constant(radconstant).definition.evaluate_as_int()
        else:
            return None

    def _get_ego_radius(self):
        if self._ego_scanned_last_round:
            return math.inf
        radconstant = self._annotation.ego_radius_constant
        if radconstant:
            return self._program.get_constant(radconstant).definition.evaluate_as_int()
        else:
            return None

    def _set_camera(self, camera_index):
        camera_constant_names = self._annotation.camera_constants(camera_index)
        viewarea_xlb = self._program.get_constant(camera_constant_names[0]).definition.evaluate_as_int()
        viewarea_ylb = self._program.get_constant(camera_constant_names[1]).definition.evaluate_as_int()
        viewarea_xub = self._program.get_constant(camera_constant_names[2]).definition.evaluate_as_int()
        viewarea_yub = self._program.get_constant(camera_constant_names[3]).definition.evaluate_as_int()
        viewarea = patches.Rectangle((viewarea_xlb, viewarea_ylb), viewarea_xub - viewarea_xlb + 1,
                                     viewarea_yub - viewarea_ylb + 1, linewidth=7, edgecolor='b', facecolor='b',
                                     alpha=0.05, hatch='o')
        self._ax.add_patch(viewarea)
        self._tmp_objects.append(viewarea)

    def _set_adv_area(self, adv_index):
        if self._annotation.adv_draw_area_boundaries:
            corner_constant_names = self._annotation.adv_area(adv_index)
            viewarea_xlb = self._program.get_constant(corner_constant_names[0]).definition.evaluate_as_int()
            viewarea_ylb = self._program.get_constant(corner_constant_names[1]).definition.evaluate_as_int()
            viewarea_xub = self._program.get_constant(corner_constant_names[2]).definition.evaluate_as_int()
            viewarea_yub = self._program.get_constant(corner_constant_names[3]).definition.evaluate_as_int()
            viewarea = patches.Rectangle((viewarea_xlb, viewarea_ylb), viewarea_xub - viewarea_xlb + 1,
                                         viewarea_yub - viewarea_ylb + 1, linewidth=2.3, edgecolor='r', fill=False, linestyle="dashed",
                                         alpha=1)
            self._ax.add_patch(viewarea)
            self._tmp_objects.append(viewarea)

    def render(self, snapshot, show_frame_count=None, show=False):
        logger.debug("start rendering")
        self._clear()
        ax = self._ax
        ego_xloc, ego_yloc = self._get_ego_loc(snapshot.state)
        ego_radius = self._get_ego_radius()


        if  self._get_action_string(snapshot.state, snapshot.action) is not None and self._get_action_string(snapshot.state, snapshot.action) == self._annotation.scan_action:
            self._ego_scanned_last_round = True
        else:
            self._ego_scanned_last_round = False
        self._set_ego(ax, ego_xloc, ego_yloc, ego_radius)

        # only for belief support traces
        if hasattr(snapshot, 'potential_states'):
            for bstate in snapshot.potential_states:
                ego_xloc_alt, ego_yloc_alt = self._get_ego_loc(bstate)
                self._set_ego_alternatives(ax, ego_xloc_alt, ego_yloc_alt)

        # allow to always see an area
        for cameraindex in range(self._annotation.nr_cameras):
            self._set_camera(cameraindex)

        # For rendering stuff like energy bars
        if self._annotation.has_resources:
            module, var = self._annotation.resource_identifiers[0]
            var = self._program.get_module(module).get_integer_variable(var).expression_variable
            resource_level = self._get_int_value(snapshot.state, var)
            max_resource_level = self._program.get_constant(self._annotation.max_resource_level_constants[0]).definition.evaluate_as_int()
            self._set_resources(float(resource_level)/float(max_resource_level))

        # For rendering all other moving obstacles
        for i in range(self._annotation.nr_adversaries):
            self._set_adv_area(i)
            adv_xloc, adv_yloc = self._get_adv_loc(snapshot.state,i)
            adv_direction = self._get_adv_direction(snapshot.state,i)
            adv_radius = self._get_adv_radius()

            self._set_adversary(adv_xloc, adv_yloc, adv_direction, adv_radius, i)
            if hasattr(snapshot, 'potential_states'):
                for bstate in snapshot.potential_states:
                    adv_xloc_alt, adv_yloc_alt = self._get_adv_loc(bstate,i)
                    self._set_adv_alternatives(adv_xloc_alt, adv_yloc_alt)

        # Determine which actions we take
        self._set_actions(snapshot.state, ego_xloc, ego_yloc, snapshot.available_actions, snapshot.considered_actions, snapshot.action)

        # For rendering obstacles that have a state (but that do not move)
        for i in range(self._annotation.nr_interactive_landmarks):
            x, y = self._get_interactive_landmark_loc(i)
            status = self._get_interactive_landmark_status(snapshot.state, i)
            belief = InteractiveLandmarkBelief.KNOWN
            for st in snapshot.potential_states:
                if status != self._get_interactive_landmark_status(st, i):
                    belief = InteractiveLandmarkBelief.QUESTIONMARK
                    break
            self._set_interactive_landmarks(x, y, status, belief, i)

        # Right bottom (number of steps so far)
        if show_frame_count:
            props = dict(boxstyle='round', facecolor='white', alpha=0.5)
            txt = self._ax_info.text(1.0, -0.01, str(show_frame_count), fontdict={'family': 'monospace'},
                                transform=self._ax_info.transAxes, fontsize=14,
                                verticalalignment='top', bbox=props)
            self._tmp_objects.append(txt)

        ax.pcolor(self._data, cmap=colors, edgecolors='k', linestyle= 'dashed', linewidths=0.2, vmin=0, vmax=7, zorder=-100)

        logger.debug("done rendering")
        if show:
            plt.show()

    def record(self, file, trace):
        if file.endswith(".gif"):
            gif = True
        else:
            gif = False

        if gif:
            moviewriter = mpl.animation.ImageMagickWriter(fps=3)
        else:
            moviewriter = mpl.animation.FFMpegWriter(fps=3)
        trace.check_validity()
        i = 1
        with moviewriter.saving(self._fig, file, dpi=100):
            it = iter(trace)
            for snapshot in tqdm(trace, total=len(trace)-1):
                self.render(snapshot, show_frame_count=i)
                moviewriter.grab_frame()
                i += 1
        self._reset()


