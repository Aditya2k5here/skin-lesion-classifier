import os
import csv
import shutil
import random

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
HAM_ARCHIVE_DIR = os.path.join(ROOT_DIR, '..', 'archive')
ISIC_ARCHIVE_DIR = os.path.join(ROOT_DIR, '..', 'archive (1)')
DATASET_DIR = os.path.join(ROOT_DIR, 'backend', 'dataset')
HAM_CSV = os.path.join(HAM_ARCHIVE_DIR, 'HAM10000_metadata.csv')
ISIC_GT_CSV = os.path.join(ISIC_ARCHIVE_DIR, 'ISIC_2019_Training_GroundTruth.csv')
ISIC_IMAGE_DIR = os.path.join(ISIC_ARCHIVE_DIR, 'ISIC_2019_Training_Input')

PHASES = ['train', 'val']
CLASSES = ['akiec', 'bcc', 'bkl', 'df', 'mel', 'nv', 'vasc']
ISIC_LABEL_MAP = {
    'AK': 'akiec',
    'BCC': 'bcc',
    'BKL': 'bkl',
    'DF': 'df',
    'MEL': 'mel',
    'NV': 'nv',
    'VASC': 'vasc'
}

# rebuild dataset directory
shutil.rmtree(DATASET_DIR, ignore_errors=True)
for phase in PHASES:
    for cls in CLASSES:
        os.makedirs(os.path.join(DATASET_DIR, phase, cls), exist_ok=True)

all_samples = []
errors = []

# HAM10000 images
if os.path.exists(HAM_CSV) and os.path.isdir(HAM_ARCHIVE_DIR):
    ham_image_paths = {}
    for part in ['HAM10000_images_part_1', 'HAM10000_images_part_2']:
        part_dir = os.path.join(HAM_ARCHIVE_DIR, part)
        if os.path.isdir(part_dir):
            for fname in os.listdir(part_dir):
                if fname.lower().endswith('.jpg'):
                    image_id = fname.replace('.jpg', '')
                    ham_image_paths[image_id] = os.path.join(part_dir, fname)

    with open(HAM_CSV, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            label = row['dx']
            if label not in CLASSES:
                continue
            img_id = row['image_id']
            src = ham_image_paths.get(img_id)
            if src:
                all_samples.append({'src': src, 'label': label, 'id': img_id})
            else:
                errors.append(f'HAM missing {img_id}')
else:
    print('WARNING: HAM10000 archive not found or incomplete.')

def find_image_folder(root_dir):
    if not os.path.isdir(root_dir):
        return None
    for dirpath, dirnames, filenames in os.walk(root_dir):
        if any(fname.lower().endswith('.jpg') for fname in filenames):
            return dirpath
    return None

# ISIC 2019 images
isic_images_root = find_image_folder(ISIC_IMAGE_DIR)
if os.path.exists(ISIC_GT_CSV) and isic_images_root:
    isic_image_paths = {}
    for dirpath, dirnames, filenames in os.walk(isic_images_root):
        for fname in filenames:
            if fname.lower().endswith('.jpg'):
                isic_image_paths[os.path.splitext(fname)[0]] = os.path.join(dirpath, fname)

    with open(ISIC_GT_CSV, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            image_name = row['image']
            label = None
            for key, mapped in ISIC_LABEL_MAP.items():
                if row.get(key, '0') == '1' or row.get(key, '0') == '1.0':
                    label = mapped
                    break
            if label is None:
                continue
            src = isic_image_paths.get(image_name)
            if not src:
                src = isic_image_paths.get(f'{image_name}_downsampled')
            if src:
                all_samples.append({'src': src, 'label': label, 'id': image_name})
            else:
                errors.append(f'ISIC missing {image_name}')
else:
    print('WARNING: ISIC2019 archive not found or incomplete.')

if not all_samples:
    raise RuntimeError('No samples found. Please verify the archive folders are extracted correctly.')

random.shuffle(all_samples)
split_index = int(len(all_samples) * 0.8)

copied = 0
for i, sample in enumerate(all_samples):
    phase = 'train' if i < split_index else 'val'
    dst = os.path.join(DATASET_DIR, phase, sample['label'], f"{sample['id']}.jpg")
    shutil.copy2(sample['src'], dst)
    copied += 1
    if copied % 2000 == 0:
        print(f'Copied {copied}/{len(all_samples)} images...')

print(f'\nDone! Total samples: {len(all_samples)}')
print(f'Copied: {copied}')
print(f"Dataset ready at {DATASET_DIR}")
if errors:
    print(f'Warnings: {len(errors)} missing files or skipped items.')
    print(errors[:20])
