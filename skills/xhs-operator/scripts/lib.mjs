import { createHash, randomBytes } from "node:crypto";
import { existsSync, mkdirSync, readFileSync, readdirSync, rmSync, statSync, writeFileSync } from "node:fs";
import { basename, extname, join, resolve } from "node:path";

export const HOME_DIR = resolve(process.env.XHS_HOME || join(process.env.HOME || "", "xiaohongshu"));
export const AUTH_FILE = join(HOME_DIR, "auth", "state.json");
export const RUNS_DIR = join(HOME_DIR, "runs");
export const VISIBILITIES = ["公开可见", "仅自己可见", "仅互关好友可见"];

export function ensureHome() {
  mkdirSync(join(HOME_DIR, "auth"), { recursive: true, mode: 0o700 });
  mkdirSync(RUNS_DIR, { recursive: true, mode: 0o700 });
}

export function readJson(path) {
  return JSON.parse(readFileSync(path, "utf8"));
}

export function writeJson(path, value) {
  writeFileSync(path, `${JSON.stringify(value, null, 2)}\n`, { mode: 0o600 });
}

export function updateState(runDir, updates) {
  const path = join(runDir, "state.json");
  const state = existsSync(path) ? readJson(path) : {};
  Object.assign(state, updates, { updatedAt: new Date().toISOString() });
  writeJson(path, state);
  return state;
}

export function newRunId(prefix = "run") {
  const stamp = new Date().toISOString().replace(/[-:]/g, "").replace(/\..+/, "");
  return `${prefix}-${stamp}-${randomBytes(3).toString("hex")}`;
}

export function confirmationToken(runId, request) {
  return createHash("sha256")
    .update(runId)
    .update(JSON.stringify(request))
    .digest("hex")
    .slice(0, 8)
    .toUpperCase();
}

export function redact(text) {
  return text
    .replace(/(?<!\d)1\d{10}(?!\d)/g, (phone) => `${phone.slice(0, 3)}****${phone.slice(-4)}`)
    .replace(/("?(?:token|cookie|authorization|password|code)"?\s*[:=]\s*)[^\s,}\]]+/gi, "$1[REDACTED]");
}

function nonEmptyString(value, name, max) {
  if (typeof value !== "string" || !value.trim()) throw new Error(`${name}不能为空`);
  if ([...value.trim()].length > max) throw new Error(`${name}不能超过${max}个字符`);
  return value.trim();
}

const IMAGE_FORMATS = {
  jpeg: { extension: ".jpg", mimeType: "image/jpeg" },
  png: { extension: ".png", mimeType: "image/png" },
  webp: { extension: ".webp", mimeType: "image/webp" },
};

export function detectImageFormat(path) {
  const header = readFileSync(path).subarray(0, 12);
  if (header.length >= 3 && header[0] === 0xff && header[1] === 0xd8 && header[2] === 0xff) return "jpeg";
  if (header.length >= 8 && header.subarray(0, 8).equals(Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]))) return "png";
  if (header.length >= 12 && header.toString("ascii", 0, 4) === "RIFF" && header.toString("ascii", 8, 12) === "WEBP") return "webp";
  return null;
}

export function imageUploadPayload(path) {
  const format = detectImageFormat(path);
  if (!format) throw new Error(`无法识别图片真实格式: ${path}`);
  const { extension, mimeType } = IMAGE_FORMATS[format];
  const originalName = basename(path);
  const currentExtension = extname(originalName);
  const stem = currentExtension ? originalName.slice(0, -currentExtension.length) : originalName;
  return {
    name: `${stem}${extension}`,
    mimeType,
    buffer: readFileSync(path),
  };
}

export function validateRequest(raw, now = new Date()) {
  if (!raw || typeof raw !== "object" || Array.isArray(raw)) throw new Error("请求必须是 JSON 对象");
  const images = raw.images;
  if (!Array.isArray(images) || images.length < 1 || images.length > 18) {
    throw new Error("images 必须包含 1 到 18 个图片路径");
  }
  for (const image of images) {
    if (typeof image !== "string" || !existsSync(image)) throw new Error(`图片不存在: ${image}`);
    if (!/\.(?:jpe?g|png|webp)$/i.test(image)) throw new Error(`不支持的图片格式: ${image}`);
    if (!detectImageFormat(image)) throw new Error(`无法识别图片真实格式: ${image}`);
  }
  const title = nonEmptyString(raw.title, "标题", 20);
  const body = typeof raw.body === "string" ? raw.body.trim() : "";
  const topics = raw.topics ?? [];
  if (!Array.isArray(topics) || topics.some((topic) => typeof topic !== "string" || !topic.trim())) {
    throw new Error("topics 必须是非空字符串数组");
  }
  const normalizedTopics = topics.map((topic) => topic.trim().replace(/^#+/, ""));
  const topicSuffix = normalizedTopics.map((topic) => `#${topic}`).join(" ");
  const combinedContent = [body, topicSuffix].filter(Boolean).join("\n\n");
  if ([...combinedContent].length > 1000) throw new Error("正文和话题合计不能超过1000个字符");

  const settings = raw.settings ?? {};
  const visibility = settings.visibility ?? "公开可见";
  if (!VISIBILITIES.includes(visibility)) throw new Error(`不支持的可见范围: ${visibility}`);
  let scheduledAt = null;
  if (settings.scheduledAt) {
    if (!/^\d{4}-\d{2}-\d{2} \d{2}:\d{2}$/.test(settings.scheduledAt)) {
      throw new Error("scheduledAt 必须使用北京时间 YYYY-MM-DD HH:mm");
    }
    scheduledAt = new Date(`${settings.scheduledAt.replace(" ", "T")}:00+08:00`);
    if (Number.isNaN(scheduledAt.valueOf()) || scheduledAt <= now) throw new Error("定时发布时间必须晚于当前时间");
  }
  const collection = settings.collection ?? null;
  if (collection?.create) {
    nonEmptyString(collection.name, "合集名称", 20);
    if (collection.description && [...collection.description].length > 50) throw new Error("合集简介不能超过50个字符");
    if (collection.confirmed !== true) throw new Error("创建合集前必须设置 collection.confirmed=true");
  }

  return {
    images: images.map((image) => resolve(image)),
    title,
    body,
    topics: normalizedTopics,
    content: body,
    settings: {
      original: settings.original === true,
      allowRemix: settings.allowRemix === true,
      allowCopy: settings.allowCopy === true,
      visibility,
      scheduledAt: scheduledAt ? settings.scheduledAt : null,
      collection,
      location: settings.location ?? null,
    },
  };
}

export function cleanupRuns(now = Date.now()) {
  ensureHome();
  const removed = [];
  for (const entry of readdirSync(RUNS_DIR, { withFileTypes: true })) {
    if (!entry.isDirectory()) continue;
    const runDir = join(RUNS_DIR, entry.name);
    const statePath = join(runDir, "state.json");
    let state = {};
    try { state = existsSync(statePath) ? readJson(statePath) : {}; } catch {}
    const successful = state.status === "published";
    const limit = (successful ? 30 : 7) * 24 * 60 * 60 * 1000;
    if (now - statSync(runDir).mtimeMs > limit) {
      rmSync(runDir, { recursive: true, force: true });
      removed.push(entry.name);
    }
  }
  return removed;
}

export function publicSummary(request) {
  return {
    title: request.title,
    body: request.body,
    topics: request.topics,
    imageCount: request.images.length,
    images: request.images.map((image) => basename(image)),
    settings: request.settings,
  };
}
