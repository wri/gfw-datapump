import io
import tifffile
import logging

from ..clients.aws import get_s3_path_parts
from ..globals import LOGGER

logging.getLogger('tifffile').setLevel(logging.CRITICAL)

def write_vrt(s3_client, s3_dest, s3_url1, s3_url2):
    """
    Create a VRT file for the COGs specified by s3_url1 and s3_url2, and write the VRT
    file to s3_dest. The function is emulating gdalbuildvrt or gdal.BuildVRT without
    having to load the large GDAL library/executables into the lambda layer.
    """

    LOGGER.info(f"write_vrt {s3_dest}, from {s3_url1}, {s3_url2}")
    m1 = get_cog_metadata(s3_client, s3_url1)
    m2 = get_cog_metadata(s3_client, s3_url2)

    # Define the VRT Master Properties
    # Usually based on the primary file or a known global extent
    vrt_gt = m1['gt']
    vrt_x_size = m1['x_size']
    vrt_y_size = m1['y_size']

    # Calculate DstRect for the second file
    # (Assuming file 1 is the base and file 2 is the 'overlap' that needs offsetting)
    x_off1, y_off1 = calculate_dst_rect(vrt_gt, m1['gt'])
    x_off2, y_off2 = calculate_dst_rect(vrt_gt, m2['gt'])

    source1 = generate_complex_source(s3_url1, m1, x_off1, y_off1)
    source2 = generate_complex_source(s3_url2, m2, x_off2, y_off2)

    vrt_xml = f"""<VRTDataset rasterXSize="{vrt_x_size}" rasterYSize="{vrt_y_size}">
  <SRS dataAxisToSRSAxisMapping="2,1">GEOGCS["WGS 84",DATUM["WGS_1984",SPHEROID["WGS 84",6378137,298.257223563]],PRIMEM["Greenwich",0],UNIT["degree",0.0174532925199433],AUTHORITY["EPSG","4326"]]</SRS>
  <GeoTransform>{vrt_gt[0]}, {vrt_gt[1]}, {vrt_gt[2]}, {vrt_gt[3]}, {vrt_gt[4]}, {vrt_gt[5]}</GeoTransform>
  <VRTRasterBand dataType="{m1['dtype']}" band="1">
    <NoDataValue>0</NoDataValue>
    <ColorInterp>Gray</ColorInterp>
{source1}
{source2}
  </VRTRasterBand>
  <OverviewList resampling="nearest">2 4 8 16 32 64 128 256 512 1024 2048</OverviewList>
</VRTDataset>"""

    bucket, key = get_s3_path_parts(s3_dest)
    LOGGER.info(f"write_vrt to {bucket}, {key}: {vrt_xml}")
    s3_client.put_object(
        Bucket=bucket,
        Key=key,
        Body=vrt_xml,
        ContentType="application/xml"
    )

def get_cog_metadata(s3_client, s3_path):
    """
    Reads only the header of the COG to get dimensions and geotransform.
    """

    bucket, key = get_s3_path_parts(s3_path)

    # Fetch just the first 64KB - usually contains all primary tags
    response = s3_client.get_object(Bucket=bucket, Key=key, Range='bytes=0-65535')
    data = io.BytesIO(response['Body'].read())

    with tifffile.TiffFile(data, omexml=False) as tif:
        page = tif.pages[0]
        tags = page.tags

        # Determine Tile/Block Size (COGs use TileWidth/TileLength)
        # Fallback to 512 if not explicitly tiled
        block_x = tags['TileWidth'].value if 'TileWidth' in tags else 512
        block_y = tags['TileLength'].value if 'TileLength' in tags else 512

        # Determine GeoTransform
        # Standard COGs use ModelTransformationTag
        if 'ModelTransformationTag' in tags:
            m = tags['ModelTransformationTag'].value
            # GDAL order: [ul_x, x_res, row_rot, ul_y, col_rot, y_res]
            gt = (m[3], m[0], 0.0, m[7], 0.0, m[5])
        elif 'ModelTiepointTag' in tags and 'ModelPixelScaleTag' in tags:
            tp = tags['ModelTiepointTag'].value[3:6]
            ps = tags['ModelPixelScaleTag'].value
            gt = (tp[0], ps[0], 0.0, tp[1], 0.0, -ps[1])
        else:
            # Absolute fallback to identity if tags are missing
            gt = (0.0, 1.0, 0.0, 0.0, 0.0, -1.0)

        return {
            "x_size": page.shape[1],
            "y_size": page.shape[0],
            "block_x": block_x,
            "block_y": block_y,
            "gt": gt,
            "dtype": str(page.dtype).replace('uint', 'UInt').replace('int', 'Int').replace('UInt8', 'Byte')
        }

def calculate_dst_rect(vrt_gt, src_gt):
    """
    Calculates pixel offsets (xOff, yOff) for the DstRect.
    """
    # xOff = (Source_Origin_X - VRT_Origin_X) / VRT_Pixel_Width
    x_off = round((src_gt[0] - vrt_gt[0]) / vrt_gt[1])
    # yOff = (Source_Origin_Y - VRT_Origin_Y) / VRT_Pixel_Height
    y_off = round((src_gt[3] - vrt_gt[3]) / vrt_gt[5])
    return x_off, y_off

def generate_complex_source(s3_path, meta, x_off, y_off):
    """
    Generates the XML string for a single ComplexSource.
    """
    vsi_path = s3_path.replace("s3://", "/vsis3/")

    return f"""    <ComplexSource>
      <SourceFilename relativeToVRT="0">{vsi_path}</SourceFilename>
      <SourceBand>1</SourceBand>
      <SourceProperties RasterXSize="{meta['x_size']}" RasterYSize="{meta['y_size']}" DataType="{meta['dtype']}" BlockXSize="{meta['block_x']}" BlockYSize="{meta['block_y']}" />
      <SrcRect xOff="0" yOff="0" xSize="{meta['x_size']}" ySize="{meta['y_size']}" />
      <DstRect xOff="{x_off}" yOff="{y_off}" xSize="{meta['x_size']}" ySize="{meta['y_size']}" />
      <NODATA>0</NODATA>
    </ComplexSource>"""
