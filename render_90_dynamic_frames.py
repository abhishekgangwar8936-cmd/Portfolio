import os
import numpy as np
from PIL import Image
from scipy.ndimage import map_coordinates

def generate_frames():
    output_dir = 'assets/images/abhishek-scroll'
    os.makedirs(output_dir, exist_ok=True)

    print('Loading Abhishek transparent cutout...')
    abh = Image.open('abhishek_transparent.png')
    
    # Scale Abhishek to fit 1280x720 canvas
    target_h = int(1024 * 0.70)
    target_w = int(1020 * 0.70)
    abh_resized = abh.resize((target_w, target_h), Image.Resampling.LANCZOS)
    abh_arr = np.array(abh_resized).astype(np.float32)

    H, W = 720, 1280
    paste_x_base = 700 - target_w // 2
    paste_y_base = 720 - target_h

    # Backdrop: Exact match to Piyush's original studio background (warm orange spotlight on left fading to dark on right)
    yy_bg, xx_bg = np.mgrid[0:H, 0:W].astype(np.float32)
    dist_sq = ((xx_bg - 50.0)/420.0)**2 + ((yy_bg - 300.0)/260.0)**2
    spotlight = np.exp(-dist_sq * 0.7)

    r_bg = 6.0 + spotlight * 230.0
    g_bg = 6.0 + spotlight * 138.0
    b_bg = 6.0 + spotlight * 62.0

    bg_arr = np.clip(np.stack([r_bg, g_bg, b_bg], axis=-1), 0, 255).astype(np.uint8)
    bg_clean = Image.fromarray(bg_arr).convert('RGBA')

    # Abhishek grid for 2.5D warping
    h_abh, w_abh = target_h, target_w
    yy_abh, xx_abh = np.mgrid[0:h_abh, 0:w_abh].astype(np.float32)

    pivot_y = 530.0
    pivot_x = w_abh / 2.0

    weight = np.clip((pivot_y - yy_abh) / (pivot_y * 0.95), 0.0, 1.0)
    weight = weight ** 1.15

    total_frames = 90
    print(f'Rendering {total_frames} frames with #121212 / #1A1A1A background and electric blue glow...')

    for i in range(total_frames):
        t = i / (total_frames - 1.0)
        
        # 1. Pitch (Nodding down & up)
        nod_wave1 = np.exp(-((t - 0.35) / 0.12)**2) * 38.0
        nod_wave2 = np.exp(-((t - 0.72) / 0.11)**2) * 24.0
        rebound = -np.sin(t * np.pi * 3.0) * 8.0
        pitch = nod_wave1 + nod_wave2 + rebound

        # 2. Yaw (Rotation / Turn Left-Right)
        yaw = np.sin(t * 2.0 * np.pi) * 32.0 + np.sin(t * 4.0 * np.pi) * 8.0

        # 3. Roll (Head Tilt angle in degrees)
        roll_deg = -np.sin(t * 2.0 * np.pi) * 3.5 - np.cos(t * np.pi) * 1.5

        # 4. Vertical perspective compression
        compress = (max(0.0, pitch) / 38.0) * 0.045

        roll_rad = np.radians(roll_deg)
        angle = roll_rad * weight
        cos_a = np.cos(angle)
        sin_a = np.sin(angle)

        dx = xx_abh - pivot_x
        dy = yy_abh - pivot_y

        r_center = np.clip(1.0 - (np.abs(dx) / (w_abh * 0.45)), 0.0, 1.0)
        parallax_yaw = yaw * weight * (0.7 + 0.6 * r_center)

        src_x = pivot_x + dx * cos_a + dy * sin_a - parallax_yaw
        src_y = pivot_y - dx * sin_a + dy * cos_a - (pitch * weight + (yy_abh - pivot_y) * compress * weight)

        warped_arr = np.zeros_like(abh_arr)
        coords = [src_y, src_x]
        for c in range(4):
            warped_arr[:, :, c] = map_coordinates(abh_arr[:, :, c], coords, order=3, mode='constant', cval=0.0)

        warped_arr = np.clip(warped_arr, 0, 255).astype(np.uint8)
        warped_img = Image.fromarray(warped_arr)

        frame_canvas = bg_clean.copy()
        paste_x = int(paste_x_base + yaw * 0.25)
        paste_y = paste_y_base
        frame_canvas.paste(warped_img, (paste_x, paste_y), warped_img)

        frame_num = i + 1
        filename = os.path.join(output_dir, f'frame-{frame_num:03d}.jpg')
        frame_canvas.convert('RGB').save(filename, 'JPEG', quality=93)

        if frame_num % 15 == 0 or frame_num == total_frames:
            print(f'Rendered frame {frame_num:02d}/{total_frames}')

    print('All 90 frames with #121212 / #1A1A1A background rendered successfully!')

if __name__ == '__main__':
    generate_frames()
