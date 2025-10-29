"""
Download NLTK Data

Downloads required NLTK data for sentiment analysis.
"""

import nltk
import sys


def download_nltk_data():
    """Download required NLTK data packages"""
    
    print("📦 Downloading NLTK data packages...\n")
    
    packages = [
        'punkt',
        'averaged_perceptron_tagger',
        'brown',
        'stopwords'
    ]
    
    success_count = 0
    failed_packages = []
    
    for package in packages:
        try:
            print(f"Downloading {package}...", end=" ")
            nltk.download(package, quiet=True)
            print("✅")
            success_count += 1
        except Exception as e:
            print(f"❌ Failed: {e}")
            failed_packages.append(package)
    
    print(f"\n{'='*60}")
    print(f"Downloaded {success_count}/{len(packages)} packages successfully")
    
    if failed_packages:
        print(f"\n⚠️  Failed packages: {', '.join(failed_packages)}")
        print("You may need to download these manually")
        return False
    else:
        print("\n✅ All NLTK data downloaded successfully!")
        return True


if __name__ == "__main__":
    try:
        success = download_nltk_data()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
