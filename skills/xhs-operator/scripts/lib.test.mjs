import assert from "node:assert/strict";
import { mkdtempSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import test from "node:test";
import { detectImageFormat, imageUploadPayload, validateRequest } from "./lib.mjs";

const JPEG = Buffer.from([0xff, 0xd8, 0xff, 0xe0, 0x00, 0x10]);
const PNG = Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]);
const WEBP = Buffer.from("RIFF0000WEBP", "ascii");

function withTempImage(name, bytes, callback) {
  const directory = mkdtempSync(join(tmpdir(), "xhs-operator-test-"));
  try {
    const path = join(directory, name);
    writeFileSync(path, bytes);
    callback(path);
  } finally {
    rmSync(directory, { recursive: true, force: true });
  }
}

test("detectImageFormat reads file signatures instead of extensions", () => {
  withTempImage("photo.png", JPEG, (path) => assert.equal(detectImageFormat(path), "jpeg"));
  withTempImage("photo.jpg", PNG, (path) => assert.equal(detectImageFormat(path), "png"));
  withTempImage("photo.jpg", WEBP, (path) => assert.equal(detectImageFormat(path), "webp"));
});

test("imageUploadPayload normalizes the upload name and MIME type", () => {
  withTempImage("photo.png", JPEG, (path) => {
    const payload = imageUploadPayload(path);
    assert.equal(payload.name, "photo.jpg");
    assert.equal(payload.mimeType, "image/jpeg");
    assert.deepEqual(payload.buffer, JPEG);
  });
});

test("validateRequest accepts a supported image by its real format", () => {
  withTempImage("photo.png", JPEG, (path) => {
    const request = validateRequest({ images: [path], title: "测试", body: "正文" });
    assert.deepEqual(request.images, [path]);
  });
});

test("validateRequest keeps topics out of the plain-text editor content", () => {
  withTempImage("photo.jpg", JPEG, (path) => {
    const request = validateRequest({
      images: [path],
      title: "测试",
      body: "正文",
      topics: ["ClawChat", "AI办公"],
    });
    assert.equal(request.content, "正文");
    assert.deepEqual(request.topics, ["ClawChat", "AI办公"]);
  });
});

test("imageUploadPayload rejects unsupported bytes before browser upload", () => {
  withTempImage("photo.png", Buffer.from("not an image"), (path) => {
    assert.throws(() => imageUploadPayload(path), /无法识别图片真实格式/);
  });
});
