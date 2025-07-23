def display_rots_and_trans(ts_and_qs):
    txs, tys, tzs, qxs, qys, qzs, qws = ts_and_qs

    txs = sorted(txs)
    tys = sorted(tys)
    tzs = sorted(tzs)
    qxs = sorted(qxs)
    qys = sorted(qys)
    qzs = sorted(qzs)
    qws = sorted(qws)

    print("Raw Values:")
    print(f"tx: {txs[0]} to {txs[-1]}")
    print(f"ty: {tys[0]} to {tys[-1]}")
    print(f"tz: {tzs[0]} to {tzs[-1]}")
    print(f"qx: {qxs[0]} to {qxs[-1]}")
    print(f"qy: {qys[0]} to {qys[-1]}")
    print(f"qz: {qzs[0]} to {qzs[-1]}")
    print(f"qw: {qws[0]} to {qws[-1]}")

    txs = sorted([abs(t) for t in txs])
    tys = sorted([abs(t) for t in tys])
    tzs = sorted([abs(t) for t in tzs])
    qxs = sorted([abs(q) for q in qxs])
    qys = sorted([abs(q) for q in qys])
    qzs = sorted([abs(q) for q in qzs])
    qws = sorted([abs(q) for q in qws])

    print("\nAbsolute Values:")
    print(f"tx: {txs[0]} to {txs[-1]}")
    print(f"ty: {tys[0]} to {tys[-1]}")
    print(f"tz: {tzs[0]} to {tzs[-1]}")
    print(f"qx: {qxs[0]} to {qxs[-1]}")
    print(f"qy: {qys[0]} to {qys[-1]}")
    print(f"qz: {qzs[0]} to {qzs[-1]}")
    print(f"qw: {qws[0]} to {qws[-1]}")

def read_images_file(filepath):
    with open(filepath) as f:
        lines = f.readlines()
    
    txs = []
    tys = []
    tzs = []
    qxs = []
    qys = []
    qzs = []
    qws = []

    xs = []
    ys = []

    read_points =  False

    line_index = -1
    for line in lines:
        line_index += 1
        if line[0] == "#":
            continue
        
        if not read_points:
            # Read rotation/translation
            image_id, qw, qx, qy, qz, tx, ty, tz, camera_id, name = line.split()
            
            qw = float(qw)
            qx = float(qx)
            qy = float(qy)
            qz = float(qz)
            tx = float(tx)
            ty = float(ty)
            tz = float(tz)

            txs.append(tx)
            tys.append(ty)
            tzs.append(tz)
            qxs.append(qx)
            qys.append(qy)
            qzs.append(qz)
            qws.append(qw)

            read_points = True
        else:
            parts = line.split(" ")
            index = 0
            for part in parts:
                if index == 0:
                    try:
                        xs.append(float(part))
                    except:
                        print("skipped line ", line_index)
                        continue
                elif index == 1:
                    ys.append(float(part))
                
                index += 1
                index = index % 3
            
            
            read_points = False


    print("Rotations and Translations")
    display_rots_and_trans([txs, tys, tzs, qxs, qys, qzs, qws])

    print(f"\nSorting {len(xs)} xs and {len(ys)} ys")
    xs = sorted(xs)
    ys = sorted(ys)
    print("Image Coordinates")
    print(f"x: {xs[0]} to {xs[-1]}")
    print(f"y: {ys[0]} to {ys[-1]}")

def read_svin_file(filepath):
    with open(filepath) as f:
        lines = f.readlines()
    
    timestamps = []
    txs = []
    tys = []
    tzs = []
    qxs = []
    qys = []
    qzs = []
    qws = []

    for line in lines:
        if line[0] == "#":
            continue
        
        timestamp, tx, ty, tz, qx, qy, qz, qw = [float(val) for val in line.split(" ")]
        
        timestamps.append(timestamp)
        txs.append(tx)
        tys.append(ty)
        tzs.append(tz)
        qxs.append(qx)
        qys.append(qy)
        qzs.append(qz)
        qws.append(qw)
    
    display_rots_and_trans([txs, tys, tzs, qxs, qys, qzs, qws])

    return [txs, tys, tzs, qxs, qys, qzs, qws]

def read_points3d_file(filepath):
    with open(filepath) as f:
        lines = f.readlines()

    xs = []
    ys = []
    zs = []
    rs = []
    gs = []
    bs = []
    errors = []

    for line in lines:
        if line[0] == "#":
            continue
        
        x, y, z = [float(c) for c in line.split(" ")[1:4]]
        r, g, b, error = [float(c) for c in line.split(" ")[4:8]]

        xs.append(x)
        ys.append(y)
        zs.append(z)
        rs.append(r)
        gs.append(g)
        bs.append(b)
        errors.append(error)
    
    xs = sorted(xs)
    ys = sorted(ys)
    zs = sorted(zs)
    rs = sorted(rs)
    gs = sorted(gs)
    bs = sorted(bs)
    errors = sorted(errors)

    print("Raw Values")
    print(f"x: {xs[0]} to {xs[-1]}")
    print(f"y: {ys[0]} to {ys[-1]}")
    print(f"z: {zs[0]} to {zs[-1]}")
    print(f"r: {rs[0]} to {rs[-1]}")
    print(f"g: {gs[0]} to {gs[-1]}")
    print(f"b: {bs[0]} to {bs[-1]}")
    print(f"error: {errors[0]} to {bs[-1]}")

    xs = sorted([abs(v) for v in xs])
    ys = sorted([abs(v) for v in ys])
    zs = sorted([abs(v) for v in zs])
    rs = sorted([abs(v) for v in rs])
    gs = sorted([abs(v) for v in gs])
    bs = sorted([abs(v) for v in bs])
    errors = sorted([abs(v) for v in errors])

    print("\nAbsolute Values")
    print(f"x: {xs[0]} to {xs[-1]}")
    print(f"y: {ys[0]} to {ys[-1]}")
    print(f"z: {zs[0]} to {zs[-1]}")
    print(f"r: {rs[0]} to {rs[-1]}")
    print(f"g: {gs[0]} to {gs[-1]}")
    print(f"b: {bs[0]} to {bs[-1]}")
    print(f"error: {errors[0]} to {bs[-1]}")

# def read_file_parts():
#     with open("/home/luke/Documents/pamir_stuff/data_test/pamir2/images.txt") as f:
#         lines = f.readlines()
    
#     with open("output.txt", "a+") as f:
#         f.write(lines[16184])
#         f.write(lines[16185])
#         f.write(lines[16186])
    
# read_file_parts()

print("Pamir 2")
print("\nSVIN.txt")
read_svin_file("/home/luke/Documents/pamir_stuff/data_test/pamir2/svin.txt")
print("\nImages.txt")
read_images_file("/home/luke/Documents/pamir_stuff/data_test/pamir2/images.txt")
print("\nPoints3d.txt")
read_points3d_file("/home/luke/Documents/pamir_stuff/data_test/pamir2/points3D.txt")