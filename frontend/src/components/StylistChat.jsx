// Purpose: Mira chat window with quick replies and preferences panel
import { useCallback, useEffect, useRef, useState } from "react";
import "./mira-chat.css";

const MAX_MESSAGE_LENGTH = 1000;

const ASSISTANT_NAME = "MIRA";

// Tappable suggestions. "photo" opens the image picker (a fit rating needs a picture).
const SUGGESTIONS = [
  { label: "What should I wear today?" },
  { label: "Style my pink shirt." },
  { label: "Build me a college fit." },
  { label: "Help me with a date-night look." },
  { label: "What colours suit my skin tone?" },
  { label: "Build an outfit from my wardrobe." },
  { label: "Style outfits for my body shape." },
  { label: "Rate my outfit.", action: "photo", draft: "Rate my fit." },
];
const INITIAL_SUGGESTIONS = 6;

// Quick replies: the model can end a message with <quick_replies>A | B | C</quick_replies>
// (or the API can return quick_replies: []). If neither is present, a few clear
// "which one?" questions get sensible answer chips, and only when MIRA actually asked.
const QUICK_REPLY_TAG = /<quick_replies>([\s\S]*?)(?:<\/quick_replies>|$)/gi;
const QUESTION_CHIPS = [
  [/occasion|dressing for|where are you (going|headed)|what.s the plan/i, ["College", "Date night", "Wedding", "Office", "Party", "Everyday"]],
  [/which vibe|what vibe|aesthetic|which style|style are we/i, ["Streetwear", "Minimalist", "Soft girl", "Old money", "Casual", "Party glam"]],
  [/skin ?tone|undertone/i, ["Fair", "Wheatish", "Tan", "Deep", "Not sure"]],
  [/body (shape|type)|silhouette|proportion/i, ["Pear", "Apple", "Hourglass", "Rectangle", "Inverted triangle", "Skip this"]],
  [/jeans/i, ["Light-wash", "Dark denim", "Black", "White"]],
];

function splitReply(content) {
  const raw = String(content || "");
  const tagged = [...raw.matchAll(QUICK_REPLY_TAG)][0];
  const options = tagged
    ? tagged[1].split(/[|\n]/).map((o) => o.replace(/^[-*\u2022\d.)\s]+/, "").trim().slice(0, 40)).filter(Boolean).slice(0, 6)
    : [];
  return { text: raw.replace(QUICK_REPLY_TAG, "").trim(), options };
}

function quickRepliesFor(message) {
  if (!message || message.role !== "assistant") return [];
  if (Array.isArray(message.quickReplies) && message.quickReplies.length) {
    return message.quickReplies.map((o) => String(o).slice(0, 40)).slice(0, 6);
  }
  const { text, options } = splitReply(message.content);
  if (options.length) return options;
  const lastLine = text.split("\n").map((l) => l.trim()).filter(Boolean).pop() || "";
  if (!lastLine.endsWith("?")) return [];
  const hit = QUESTION_CHIPS.find(([pattern]) => pattern.test(lastLine));
  return hit ? hit[1] : [];
}

const CATEGORY_OPTIONS = ["Men's", "Women's", "Unisex", "Traditional Indian", "Western"];
const ADVICE_OPTIONS = ["Jeans", "Trousers", "Shirts & tops", "Kurtis", "Dresses", "Sarees", "Lehenga-choli", "Salwar suits", "Indo-Western"];
const FIT_OPTIONS = ["Relaxed", "Regular", "Slim", "Oversized", "Structured"];
const OCCASION_OPTIONS = ["College", "Office", "Casual outings", "Parties", "Weddings", "Festivals"];
const PROPORTION_OPTIONS = [
  ["", "Prefer not to say"],
  ["unsure", "Not sure"],
  ["pear-shaped", "Pear-shaped"],
  ["apple-shaped", "Apple-shaped"],
  ["hourglass", "Hourglass"],
  ["rectangle", "Rectangle"],
  ["inverted triangle", "Inverted triangle"],
];
const TOPIC_LABELS = {
  clothing_categories: "Clothing categories",
  height_cm: "Height",
  body_proportions: "Body proportions",
  preferred_fits: "Fits",
  favorite_colors: "Colors",
  advice_categories: "Advice categories",
  occasions: "Occasions",
  budget: "Budget",
  comfort_notes: "Comfort",
  dislikes: "Dislikes",
};

const EMPTY_PREFS = {
  clothing_categories: [],
  height_cm: null,
  body_proportions: null,
  preferred_fits: [],
  favorite_colors: [],
  advice_categories: [],
  occasions: [],
  budget: null,
  comfort_notes: null,
  dislikes: [],
  skipped_topics: [],
};

function normalizePrefs(raw) {
  return { ...EMPTY_PREFS, ...(raw || {}) };
}

function parseList(text) {
  const seen = new Set();
  return String(text || "")
    .split(",")
    .map((item) => item.trim().slice(0, 40))
    .filter((item) => {
      const key = item.toLowerCase();
      if (!item || seen.has(key)) return false;
      seen.add(key);
      return true;
    })
    .slice(0, 12);
}

function friendlyError(status, data, validationMessage) {
  if (status === 401) return "Your session has expired. Please log in again.";
  if (status === 422) return validationMessage;
  if (typeof data?.detail === "string" && status >= 500) return data.detail;
  return "Something went wrong. Please try again.";
}

async function apiRequest(apiUrl, token, path, options = {}, validationMessage = "Please check your input and try again.") {
  let response;
  try {
    response = await fetch(`${apiUrl}${path}`, {
      ...options,
      headers: {
        Authorization: `Bearer ${token}`,
        ...(options.body ? { "Content-Type": "application/json" } : {}),
      },
    });
  } catch (error) {
    if (error.name === "AbortError") throw error;
    throw new Error("Can't reach the server. Check your connection and try again.");
  }

  let data = null;
  try {
    data = await response.json();
  } catch {
    data = null;
  }
  if (!response.ok) {
    const error = new Error(friendlyError(response.status, data, validationMessage));
    error.status = response.status;
    throw error;
  }
  return data;
}

// ---- Message rendering (plain React elements, no HTML injection) ----

function renderInline(text) {
  return text.split(/(\*\*[^*]+\*\*)/g).map((part, index) =>
    part.length > 4 && part.startsWith("**") && part.endsWith("**")
      ? <strong key={index}>{part.slice(2, -2)}</strong>
      : part
  );
}

function MessageText({ content }) {
  const cleanedContent = splitReply(content).text.replace(
    /<wardrobe_access\b[^>]*>[\s\S]*?<\/wardrobe_access>/gi,
    ""
  );
  const blocks = [];
  let list = null;

  cleanedContent.split("\n").forEach((line) => {
    const item = line.match(/^\s*(?:[-*\u2022]|\d+[.)])\s+(.*)$/);
    if (item) {
      const ordered = /^\s*\d/.test(line);
      if (!list || list.ordered !== ordered) {
        list = { type: "list", ordered, items: [] };
        blocks.push(list);
      }
      list.items.push(item[1]);
      return;
    }
    list = null;
    const heading = line.match(/^#{1,6}\s+(.*)$/);
    if (heading) blocks.push({ type: "heading", text: heading[1] });
    else if (line.trim()) blocks.push({ type: "paragraph", text: line.trim() });
  });

  return blocks.map((block, index) => {
    if (block.type === "list") {
      const Tag = block.ordered ? "ol" : "ul";
      return <Tag key={index}>{block.items.map((text, i) => <li key={i}>{renderInline(text)}</li>)}</Tag>;
    }
    if (block.type === "heading") return <p key={index}><strong>{renderInline(block.text)}</strong></p>;
    return <p key={index}>{renderInline(block.text)}</p>;
  });
}

// ---- Preferences panel ----

function ChipGroup({ label, options, values, onChange }) {
  const lowered = (value) => value.toLowerCase();
  const extras = values.filter((v) => !options.some((o) => lowered(o) === lowered(v)));
  const isOn = (option) => values.some((v) => lowered(v) === lowered(option));
  const toggle = (option) =>
    onChange(isOn(option) ? values.filter((v) => lowered(v) !== lowered(option)) : [...values, option]);

  return (
    <fieldset className="vsc-field">
      <legend>{label}</legend>
      <div className="vsc-chips">
        {[...options, ...extras].map((option) => (
          <button
            key={option}
            type="button"
            className={`vsc-chip${isOn(option) ? " on" : ""}`}
            aria-pressed={isOn(option)}
            onClick={() => toggle(option)}
          >
            {option}
          </button>
        ))}
      </div>
    </fieldset>
  );
}

function PreferencesPanel({ prefs, busy, message, onSave, onReset, onClose }) {
  const [draft, setDraft] = useState(() => ({
    clothing_categories: [...prefs.clothing_categories],
    height: prefs.height_cm == null ? "" : String(prefs.height_cm),
    body_proportions: prefs.body_proportions || "",
    preferred_fits: [...prefs.preferred_fits],
    favorite_colors: prefs.favorite_colors.join(", "),
    advice_categories: [...prefs.advice_categories],
    occasions: [...prefs.occasions],
    budget: prefs.budget || "",
    comfort_notes: prefs.comfort_notes || "",
    dislikes: prefs.dislikes.join(", "),
    skipped_topics: [...prefs.skipped_topics],
  }));
  const [heightError, setHeightError] = useState("");

  const set = (field) => (value) => setDraft((current) => ({ ...current, [field]: value }));
  const proportionOptions = PROPORTION_OPTIONS.some(([value]) => value === draft.body_proportions)
    ? PROPORTION_OPTIONS
    : [...PROPORTION_OPTIONS, [draft.body_proportions, draft.body_proportions]];

  const submit = (event) => {
    event.preventDefault();
    let height = null;
    if (draft.height.trim() !== "") {
      height = Number(draft.height);
      if (!Number.isInteger(height) || height < 100 || height > 250) {
        setHeightError("Enter a height between 100 and 250 cm, or leave it blank.");
        return;
      }
    }
    setHeightError("");
    onSave({
      clothing_categories: draft.clothing_categories,
      height_cm: height,
      body_proportions: draft.body_proportions || null,
      preferred_fits: draft.preferred_fits,
      favorite_colors: parseList(draft.favorite_colors),
      advice_categories: draft.advice_categories,
      occasions: draft.occasions,
      budget: draft.budget.trim() || null,
      comfort_notes: draft.comfort_notes.trim() || null,
      dislikes: parseList(draft.dislikes),
      skipped_topics: draft.skipped_topics,
    });
  };

  return (
    <aside className="vsc-panel" aria-label="Stylist preferences">
      <div className="vsc-panel-head">
        <h2>Style preferences</h2>
        <button type="button" className="vsc-link" onClick={onClose}>Close</button>
      </div>
      <p className="vsc-note">
        Everything here is optional. Share only what you are comfortable with. It is used only to
        personalise your advice, and you can change or reset it any time.
      </p>

      <form onSubmit={submit} noValidate>
        <ChipGroup label="Clothing you prefer" options={CATEGORY_OPTIONS} values={draft.clothing_categories} onChange={set("clothing_categories")} />
        <ChipGroup label="Advice you want" options={ADVICE_OPTIONS} values={draft.advice_categories} onChange={set("advice_categories")} />
        <ChipGroup label="Fits you like" options={FIT_OPTIONS} values={draft.preferred_fits} onChange={set("preferred_fits")} />
        <ChipGroup label="Occasions" options={OCCASION_OPTIONS} values={draft.occasions} onChange={set("occasions")} />

        <div className="vsc-field">
          <label htmlFor="vsc-colors">Colors you enjoy</label>
          <input id="vsc-colors" type="text" value={draft.favorite_colors} onChange={(e) => set("favorite_colors")(e.target.value)} placeholder="e.g. olive, navy, mustard" maxLength={300} />
        </div>

        <div className="vsc-row">
          <div className="vsc-field">
            <label htmlFor="vsc-height">Height (cm)</label>
            <input id="vsc-height" type="number" inputMode="numeric" min="100" max="250" value={draft.height} onChange={(e) => set("height")(e.target.value)} placeholder="Optional" />
          </div>
          <div className="vsc-field">
            <label htmlFor="vsc-proportions">General proportions</label>
            <select id="vsc-proportions" value={draft.body_proportions} onChange={(e) => set("body_proportions")(e.target.value)}>
              {proportionOptions.map(([value, label]) => <option key={value || "none"} value={value}>{label}</option>)}
            </select>
          </div>
        </div>
        {heightError && <div className="vsc-field-error" role="alert">{heightError}</div>}

        <div className="vsc-field">
          <label htmlFor="vsc-budget">Budget</label>
          <input id="vsc-budget" type="text" value={draft.budget} onChange={(e) => set("budget")(e.target.value)} placeholder="Optional, e.g. under 2000" maxLength={60} />
        </div>
        <div className="vsc-field">
          <label htmlFor="vsc-comfort">Comfort needs</label>
          <textarea id="vsc-comfort" rows={2} value={draft.comfort_notes} onChange={(e) => set("comfort_notes")(e.target.value)} placeholder="e.g. breathable fabrics, nothing tight at the waist" maxLength={300} />
        </div>
        <div className="vsc-field">
          <label htmlFor="vsc-dislikes">Styles you dislike</label>
          <input id="vsc-dislikes" type="text" value={draft.dislikes} onChange={(e) => set("dislikes")(e.target.value)} placeholder="e.g. crop tops, heavy embroidery" maxLength={300} />
        </div>

        {draft.skipped_topics.length > 0 && (
          <div className="vsc-field">
            <div className="vsc-skipped">
              You skipped: {draft.skipped_topics.map((t) => TOPIC_LABELS[t] || t).join(", ")}.{" "}
              <button type="button" className="vsc-link" onClick={() => set("skipped_topics")([])}>Let the stylist ask again</button>
            </div>
          </div>
        )}

        {message.text && (
          <div className={`vsc-msg ${message.type}`} role={message.type === "error" ? "alert" : "status"}>{message.text}</div>
        )}

        <div className="vsc-panel-actions">
          <button type="submit" className="vsc-btn" disabled={busy}>{busy ? "Saving…" : "Save preferences"}</button>
          <button type="button" className="vsc-btn ghost danger" disabled={busy} onClick={onReset}>Reset all</button>
        </div>
      </form>
    </aside>
  );
}

// ---- Main component ----

export default function StylistChat({ apiUrl, token, onOpenStyleMe, userName }) {
  const [messages, setMessages] = useState([]);
  const [prefs, setPrefs] = useState(EMPTY_PREFS);
  const [input, setInput] = useState("");
  const [attachedImage, setAttachedImage] = useState(null);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState("");
  const [sending, setSending] = useState(false);
  const [error, setError] = useState("");
  const [failedText, setFailedText] = useState("");
  const [prefsOpen, setPrefsOpen] = useState(false);
  const [prefsBusy, setPrefsBusy] = useState(false);
  const [prefsMessage, setPrefsMessage] = useState({ type: "", text: "" });
  const [panelKey, setPanelKey] = useState(0);
  const [showAllIdeas, setShowAllIdeas] = useState(false);
  const fileInputRef = useRef(null);
  const firstName = String(userName || "").trim().split(/\s+/)[0];

  const idRef = useRef(0);
  const listRef = useRef(null);
  const controllerRef = useRef(null);

  const loadInitial = useCallback(async (signal) => {
    setLoading(true);
    setLoadError("");
    const [history, preferences] = await Promise.allSettled([
      apiRequest(apiUrl, token, "/stylist/history?limit=50", { signal }),
      apiRequest(apiUrl, token, "/stylist/preferences", { signal }),
    ]);
    if (signal.aborted) return;

    if (history.status === "fulfilled") {
      setMessages((history.value.messages || []).map((m) => ({ id: ++idRef.current, role: m.role, content: m.content })));
    }
    if (preferences.status === "fulfilled") setPrefs(normalizePrefs(preferences.value));
    const failed = [history, preferences].find((r) => r.status === "rejected");
    if (failed) setLoadError(failed.reason.message);
    setLoading(false);
  }, [apiUrl, token]);

  useEffect(() => {
    if (!token) return undefined;
    const controller = new AbortController();
    controllerRef.current = controller;
    loadInitial(controller.signal);
    return () => controller.abort();
  }, [token, loadInitial]);

  useEffect(() => {
    const list = listRef.current;
    if (list) list.scrollTop = list.scrollHeight;
  }, [messages, sending, loading]);

  const sendMessage = useCallback(async (rawText) => {
    const text = (rawText || "").trim();
    const imageToSend = attachedImage;
    if ((!text && !imageToSend) || sending || loading) return;
    if (text.length > MAX_MESSAGE_LENGTH) {
      setError(`Please keep your message under ${MAX_MESSAGE_LENGTH} characters.`);
      return;
    }

    const userId = ++idRef.current;
    setError("");
    setFailedText("");
    setMessages((prev) => [...prev, { id: userId, role: "user", content: text || "Please analyze this image.", imagePreview: imageToSend?.preview || null }]);
    setInput("");
    setAttachedImage(null);
    setSending(true);

    try {
      const data = await apiRequest(
        apiUrl,
        token,
        "/stylist/chat",
        { method: "POST", body: JSON.stringify({
          message: text || "Please analyze the attached fashion image and suggest suitable styling options.",
          ...(imageToSend ? { image_base64: imageToSend.base64, image_mime_type: imageToSend.mimeType } : {}),
        }), signal: controllerRef.current?.signal },
        `Please type a message of up to ${MAX_MESSAGE_LENGTH} characters.`
      );
      setMessages((prev) => [
        ...prev,
        { id: ++idRef.current, role: "assistant", content: data.reply, suggestStyleMe: Boolean(data.suggest_style_me), wardrobeUsed: Boolean(data.wardrobe_used), quickReplies: Array.isArray(data.quick_replies) ? data.quick_replies : null },
      ]);
      if (data.preferences) setPrefs(normalizePrefs(data.preferences));
      if (data.preferences_updated) setPrefsMessage({ type: "info", text: "Your style preferences were updated from this chat." });
    } catch (err) {
      if (err.name === "AbortError") return;
      // The server saves nothing on failure, so drop the unsent bubble and keep the text for a retry.
      setMessages((prev) => prev.filter((m) => m.id !== userId));
      setFailedText(text);
      setInput((current) => current || text);
      setError(err.message);
    } finally {
      setSending(false);
    }
  }, [apiUrl, token, sending, loading, attachedImage]);

  const handleImageSelect = (event) => {
    const file = event.target.files?.[0];
    event.target.value = "";
    if (!file) return;
    if (!["image/jpeg", "image/png", "image/webp"].includes(file.type)) {
      setError("Choose a JPG, PNG, or WebP image."); return;
    }
    if (file.size > 5 * 1024 * 1024) {
      setError("Image must be smaller than 5 MB."); return;
    }
    const reader = new FileReader();
    reader.onload = () => {
      const result = String(reader.result || "");
      const base64 = result.split(",")[1];
      if (!base64) { setError("Could not read that image."); return; }
      setAttachedImage({ base64, mimeType: file.type, preview: result, name: file.name });
      setError("");
    };
    reader.onerror = () => setError("Could not read that image.");
    reader.readAsDataURL(file);
  };


  const handleSubmit = (event) => {
    event.preventDefault();
    sendMessage(input);
  };

  const handleKeyDown = (event) => {
    if (event.key === "Enter" && !event.shiftKey && !event.nativeEvent.isComposing) {
      event.preventDefault();
      sendMessage(input);
    }
  };

  const savePrefs = async (payload) => {
    setPrefsBusy(true);
    setPrefsMessage({ type: "", text: "" });
    try {
      const saved = await apiRequest(
        apiUrl,
        token,
        "/stylist/preferences",
        { method: "PUT", body: JSON.stringify(payload), signal: controllerRef.current?.signal },
        "Some preferences look invalid. Please check them and try again."
      );
      setPrefs(normalizePrefs(saved));
      setPrefsMessage({ type: "success", text: "Preferences saved." });
    } catch (err) {
      if (err.name !== "AbortError") setPrefsMessage({ type: "error", text: err.message });
    } finally {
      setPrefsBusy(false);
    }
  };

  const resetPrefs = async () => {
    if (!window.confirm("Reset all your saved style preferences?")) return;
    setPrefsBusy(true);
    setPrefsMessage({ type: "", text: "" });
    try {
      await apiRequest(apiUrl, token, "/stylist/preferences", { method: "DELETE", signal: controllerRef.current?.signal });
      setPrefs(EMPTY_PREFS);
      setPanelKey((key) => key + 1);
      setPrefsMessage({ type: "success", text: "Preferences cleared." });
    } catch (err) {
      if (err.name !== "AbortError") setPrefsMessage({ type: "error", text: err.message });
    } finally {
      setPrefsBusy(false);
    }
  };

  const clearChat = async () => {
    if (!window.confirm("Delete this chat history?")) return;
    try {
      await apiRequest(apiUrl, token, "/stylist/history", { method: "DELETE", signal: controllerRef.current?.signal });
      setMessages([]);
      setError("");
      setFailedText("");
    } catch (err) {
      if (err.name !== "AbortError") setError(err.message);
    }
  };

  const pickSuggestion = (item) => {
    if (item.action === "photo") {
      setInput(item.draft || item.label);
      fileInputRef.current?.click();
      return;
    }
    sendMessage(item.label);
  };

  const lastMessage = messages[messages.length - 1];
  const quickReplies = !sending && !loading ? quickRepliesFor(lastMessage) : [];
  const showStarters = !loading && messages.length === 0 && !sending;

  return (
    <section className="vsc">
      <div className={`vsc-layout${prefsOpen ? " with-panel" : ""}`}>
        <div className="vsc-chat">
          <div className="vsc-chat-top">
            <h2 className="vsc-sr">{ASSISTANT_NAME} — Your Personal AI Stylist</h2>
            <button type="button" className="vsc-prefs-btn" aria-expanded={prefsOpen} onClick={() => { setPrefsMessage({ type: "", text: "" }); setPrefsOpen((open) => !open); }}>✦ Style preferences</button>
            {messages.length > 0 && (
              <button type="button" className="vsc-link" onClick={clearChat}>Clear chat</button>
            )}
          </div>

          <div className="vsc-messages" ref={listRef} role="log" aria-live="polite" aria-label={`Conversation with ${ASSISTANT_NAME}`}>
            {loading && <div className="vsc-status">Loading your chat…</div>}

            {loadError && (
              <div className="vsc-msg error" role="alert">
                {loadError}{" "}
                <button type="button" className="vsc-link" onClick={() => loadInitial(controllerRef.current.signal)}>Retry</button>
              </div>
            )}

            {showStarters && (
              <div className="vsc-welcome">
                <div className="vsc-welcome-avatar" aria-hidden="true">M</div>
                <h3>{firstName ? `Hey, ${firstName}!` : "Hey there!"}</h3>
                <p className="vsc-welcome-lead">I’m {ASSISTANT_NAME}, your personal style bestie.</p>
                <p>Tell me the vibe, the occasion, or what you’re wearing. Let’s build a fit that feels like <strong>YOU</strong>.</p>
                <div className="vsc-suggest" role="group" aria-label="Suggested questions">
                  {(showAllIdeas ? SUGGESTIONS : SUGGESTIONS.slice(0, INITIAL_SUGGESTIONS)).map((item) => (
                    <button key={item.label} type="button" className="vsc-suggest-chip" onClick={() => pickSuggestion(item)}>{item.label}</button>
                  ))}
                </div>
                {!showAllIdeas && SUGGESTIONS.length > INITIAL_SUGGESTIONS && (
                  <button type="button" className="vsc-link" onClick={() => setShowAllIdeas(true)}>More ideas</button>
                )}
              </div>
            )}

            {messages.map((message) => (
              <div key={message.id} className={`vsc-row-msg ${message.role}`}>
                {message.role === "assistant" && <span className="vsc-avatar" aria-hidden="true">M</span>}
                <div className={`vsc-bubble ${message.role}`}>
                  {message.role === "assistant" ? <MessageText content={message.content} /> : <><p>{message.content}</p>{message.imagePreview && <img className="vsc-image-preview" src={message.imagePreview} alt="Image you shared with your stylist" />}</>}
                  {message.wardrobeUsed && <div className="vsc-source">Used your saved wardrobe</div>}
                  {message.suggestStyleMe && onOpenStyleMe && (
                    <button type="button" className="vsc-btn small" onClick={onOpenStyleMe}>Open Style Me</button>
                  )}
                </div>
              </div>
            ))}

            {quickReplies.length > 0 && (
              <div className="vsc-quick" role="group" aria-label="Quick replies">
                {quickReplies.map((option) => (
                  <button key={option} type="button" className="vsc-quick-chip" onClick={() => sendMessage(option)}>{option}</button>
                ))}
              </div>
            )}

            {sending && (
              <div className="vsc-row-msg assistant">
                <span className="vsc-avatar" aria-hidden="true">M</span>
                <div className="vsc-bubble assistant vsc-typing" aria-label={`${ASSISTANT_NAME} is typing`}>
                  <span /><span /><span />
                </div>
              </div>
            )}
          </div>

          {error && (
            <div className="vsc-msg error vsc-chat-error" role="alert">
              {error}{" "}
              {failedText && <button type="button" className="vsc-link" onClick={() => sendMessage(failedText)}>Try again</button>}
            </div>
          )}

          <form className="vsc-composer" onSubmit={handleSubmit}>
            <label className="vsc-upload-btn" title="Upload a fashion image">＋ Photo<input ref={fileInputRef} type="file" accept="image/jpeg,image/png,image/webp" onChange={handleImageSelect} /></label>
            <label htmlFor="vsc-input" className="vsc-sr">Message {ASSISTANT_NAME}</label>
            <textarea
              id="vsc-input"
              rows={1}
              value={input}
              maxLength={MAX_MESSAGE_LENGTH}
              placeholder={attachedImage ? `Ask ${ASSISTANT_NAME} about this image…` : `Ask ${ASSISTANT_NAME} about your next fit…`}
              onChange={(event) => setInput(event.target.value)}
              onKeyDown={handleKeyDown}
              disabled={loading}
            />
            <button type="submit" className="vsc-btn" disabled={sending || loading || (!input.trim() && !attachedImage)}>
              {sending ? "…" : "Send"}
            </button>
          </form>
          {attachedImage && <div className="vsc-attachment"><img src={attachedImage.preview} alt="Selected upload preview" /><span>{attachedImage.name}</span><button type="button" className="vsc-link" onClick={() => setAttachedImage(null)}>Remove</button></div>}
          <div className="vsc-hint">
            <span>Enter to send, Shift+Enter for a new line</span>
            <span>{input.length}/{MAX_MESSAGE_LENGTH}</span>
          </div>
        </div>

        {prefsOpen && (
          <PreferencesPanel
            key={panelKey}
            prefs={prefs}
            busy={prefsBusy}
            message={prefsMessage}
            onSave={savePrefs}
            onReset={resetPrefs}
            onClose={() => setPrefsOpen(false)}
          />
        )}
      </div>
    </section>
  );
}