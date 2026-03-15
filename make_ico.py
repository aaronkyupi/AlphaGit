from PIL import Image
import os
import sys


def create_icon():
    print("🎨 Dynamic ICO Generator (Max Resolution)")
    print("-" * 40)

    input_file = input("Enter the input image file name (e.g., logo.png): ").strip()

    if not os.path.exists(input_file):
        print(f"❌ Error: Could not find '{input_file}'")
        sys.exit(1)

    # Automatically append "_hq" to bust the Windows Icon Cache!
    base_name, _ = os.path.splitext(input_file)
    output_file = f"{base_name}.ico"

    try:
        print(f"🔄 Processing '{input_file}'...")
        img = Image.open(input_file)

        # 🛑 PROTOTYPE CHECK: Verify source resolution
        width, height = img.size
        if width < 256 or height < 256:
            print(f"⚠️ WARNING: Your source image is only {width}x{height} pixels.")
            print("⚠️ The resulting icon will look blurry. Use a PNG that is at least 256x256!")
        if width != height:
            print("⚠️ WARNING: Your image is not a perfect square. It will look squished.")

        # Save with maximum resolution and fallback sizes
        img.save(
            output_file,
            format="ICO",
            sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
        )

        print(f"✅ Success! Saved maximum resolution icon as: '{output_file}'")

    except Exception as e:
        print(f"❌ An error occurred: {e}")


if __name__ == "__main__":
    create_icon()