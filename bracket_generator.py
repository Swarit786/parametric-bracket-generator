import adsk.core, adsk.fusion, traceback, csv

def build_plate(design, rootComp, length, width, thickness, num_holes, hole_radius, margin, export_path):
    # clear previous part (bodies AND sketches, so rows don't stack)
    for body in list(rootComp.bRepBodies):
        body.deleteMe()
    for sk in list(rootComp.sketches):
        sk.deleteMe()

    extrudes = rootComp.features.extrudeFeatures

    # the plate
    plate_sketch = rootComp.sketches.add(rootComp.xYConstructionPlane)
    p1 = adsk.core.Point3D.create(0, 0, 0)
    p2 = adsk.core.Point3D.create(length, width, 0)
    plate_sketch.sketchCurves.sketchLines.addTwoPointRectangle(p1, p2)
    plate_prof = plate_sketch.profiles.item(0)
    plate_in = extrudes.createInput(plate_prof, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
    plate_in.setDistanceExtent(False, adsk.core.ValueInput.createByReal(thickness))
    extrudes.add(plate_in)

    # the holes — draw circles in a loop
    hole_sketch = rootComp.sketches.add(rootComp.xYConstructionPlane)
    circles = hole_sketch.sketchCurves.sketchCircles
    y_center = width / 2
    spacing  = (length - 2 * margin) / (num_holes - 1)
    for i in range(num_holes):
        x = margin + i * spacing
        center = adsk.core.Point3D.create(x, y_center, 0)
        circles.addByCenterRadius(center, hole_radius)

    # gather circle profiles, then cut through
    holes_to_cut = adsk.core.ObjectCollection.create()
    for prof in hole_sketch.profiles:
        holes_to_cut.add(prof)
    cut_in = extrudes.createInput(holes_to_cut, adsk.fusion.FeatureOperations.CutFeatureOperation)
    cut_in.setDistanceExtent(False, adsk.core.ValueInput.createByReal(thickness))
    extrudes.add(cut_in)

    # export this part to its own file
    exportMgr = design.exportManager
    opts = exportMgr.createSTEPExportOptions(export_path, rootComp)
    exportMgr.execute(opts)


def run(context):
    ui = None
    try:
        app = adsk.core.Application.get()
        ui = app.userInterface
        design = adsk.fusion.Design.cast(app.activeProduct)
        rootComp = design.rootComponent

        csv_path = 'C:/Users/swari/Desktop/parts.csv'
        with open(csv_path, newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # CSV is in mm (human-friendly) -> convert to cm for Fusion
                build_plate(
                    design, rootComp,
                    length     = float(row['length']) / 10,
                    width      = float(row['width']) / 10,
                    thickness  = float(row['thickness']) / 10,
                    num_holes  = int(row['num_holes']),
                    hole_radius= float(row['hole_radius']) / 10,
                    margin     = float(row['margin']) / 10,
                    export_path= 'C:/Users/swari/Desktop/' + row['name'] + '.step'
                )

        ui.messageBox('Done — all parts exported.')
    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))