package handlers

import (
	"archive/zip"
	"context"
	"io"
	"os"
	"path/filepath"
	"strings"

	"github.com/anomalyco/mooaws/api/ingest"
	"github.com/gofiber/fiber/v2"
)

func UploadAndIngest(c *fiber.Ctx) error {
	form, err := c.MultipartForm()
	if err != nil {
		return c.Status(400).JSON(fiber.Map{"error": "missing files"})
	}

	files := form.File["files"]
	if len(files) == 0 {
		return c.Status(400).JSON(fiber.Map{"error": "no files uploaded"})
	}

	tmpDir, err := os.MkdirTemp("", "mooaws-upload-*")
	if err != nil {
		return c.Status(500).JSON(fiber.Map{"error": "cannot create temp dir"})
	}
	defer os.RemoveAll(tmpDir)

	extractDir := filepath.Join(tmpDir, "extracted")
	os.MkdirAll(extractDir, 0755)

	for _, fh := range files {
		f, err := fh.Open()
		if err != nil {
			continue
		}

		name := strings.ToLower(fh.Filename)

		if strings.HasSuffix(name, ".zip") {
			// Save zip, then extract
			zipPath := filepath.Join(tmpDir, fh.Filename)
			out, err := os.Create(zipPath)
			if err != nil {
				f.Close()
				continue
			}
			io.Copy(out, f)
			out.Close()
			f.Close()

			zr, err := zip.OpenReader(zipPath)
			if err != nil {
				continue
			}
			for _, zf := range zr.File {
				if zf.FileInfo().IsDir() {
					continue
				}
				dest := filepath.Join(extractDir, filepath.Base(zf.Name))
				rc, err := zf.Open()
				if err != nil {
					continue
				}
				w, err := os.Create(dest)
				if err != nil {
					rc.Close()
					continue
				}
				io.Copy(w, rc)
				w.Close()
				rc.Close()
			}
			zr.Close()
		} else if strings.HasSuffix(name, ".json") {
			// Save JSON directly
			dest := filepath.Join(extractDir, fh.Filename)
			w, err := os.Create(dest)
			if err != nil {
				f.Close()
				continue
			}
			io.Copy(w, f)
			w.Close()
			f.Close()
		} else {
			f.Close()
		}
	}

	ing := ingest.New(extractDir)
	if err := ing.Run(context.Background()); err != nil {
		return c.Status(500).JSON(fiber.Map{"error": err.Error()})
	}

	return c.JSON(fiber.Map{"status": "ok", "message": "Upload ingested"})
}
