library(lidR)
library(parallel)
library(raster)
library(sf)

args <- commandArgs(trailingOnly=TRUE)
cat('running script with parameters ', args, '\n')
cat('current working directory ', getwd(), '\n')
data_path <- args[1] # path to folder containing tiles or canopy height models
ws <- as.numeric(args[2]) # window size 5
hmin <- as.numeric(args[3]) # minimum height
outdir <- args[4] # output directory
files <- list.files(path=data_path, pattern="*.tif", full.names=TRUE, recursive=FALSE)
cat(length(files), ' files in folder ', data_path, '\n')

getTtopsAndContours <- function(filename, ws, hmin, outdir) {
    # Should do the same than itcIMG
    cat('processing file ', filename, '\n')

    tile_id <- sub(pattern="(.*)\\..*$", replacement="\\1", basename(filename))
    ttop_dsn <- paste0(outdir, 'ttops/', tile_id, '.geojson')
    crown_dsn <- paste0(outdir, 'crowns/', tile_id, '.geojson')

    tile <- stack(filename) # Read multiband .tif file
    chm <- tile[[461]] # Select CHM Channel
    chm <- focal(chm, w=matrix(1,3,3), data=chm[,], fun=function(x){mean(x, na.rm=T)}) #Smoothen chm
    chm[is.na(chm[])] <- 0 # Set NA values as zero

    # Find treetops and crowns
    ttops <- locate_trees(chm, lmf(ws=ws, hmin=hmin, shape='circular'))
    algo <- dalponte2016(chm, ttops, th_tree=hmin, th_seed=0.65, th_cr=0.5, max_cr=5)
    crowns <- algo()
    crowns.shp <- rasterToPolygons(crowns, n=4, na.rm=TRUE, digits=12, dissolve=TRUE)

    # Postprocessing
    names(crowns.shp) <- "value"
    HyperCrowns <- crowns.shp[crowns.shp$'value' != 0, ]
    HyperCrowns$X <- round(coordinates(HyperCrowns)[, 1], 2)
    HyperCrowns$Y <- round(coordinates(HyperCrowns)[, 2], 2)
    HyperCrowns$Height_m <- round(raster::extract(chm, HyperCrowns, fun=max)[, 1], 2)
    HCbuf <- st_buffer(st_as_sf(HyperCrowns), dist = -res(chm)[1]/2, endCapStyle='SQUARE')
    ITCcv <- st_convex_hull(HCbuf)
    ITCcvSD <- st_sf(data.frame(ITCcv, CA_m2 = round(st_area(ITCcv), 2)))
    ITCcvSD <- ITCcvSD[ITCcvSD$CA_m2 > 1, ]
    st_crs(ITCcvSD) <- st_crs("+init=epsg:32635")
    ttops <- st_as_sf(ttops)
    st_crs(ttops) <- st_crs("+init=epsg:32635")

    tile_id <- sub(pattern="(.*)\\..*$", replacement="\\1", basename(filename))
    ttop_dsn <- paste0(outdir, 'ttops/', tile_id, '.geojson')
    crown_dsn <- paste0(outdir, 'crowns/', tile_id, '.geojson')

    sf::st_write(ttops, ttop_dsn, driver = "GeoJSON", append=FALSE)
    sf::st_write(ITCcvSD, crown_dsn, driver = "GeoJSON", append=FALSE)
    return()
}

mclapply(files, getTtopsAndContours, ws=ws, hmin=hmin, outdir=outdir, mc.cores=20)
