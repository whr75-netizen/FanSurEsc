import sys
from pathlib import Path
sys.argv=[sys.argv[0],'fixed6']
import review_curve81 as review
review.G=Path(__file__).resolve().parent/'face83/fix1';review.C=review.G/'capture';review.RASTER_SOURCE83=True
if __name__=='__main__':review.main()
