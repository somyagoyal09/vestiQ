// VESTIQ_DASHBOARD_MOOD_V2 — dashboard + daily mood only; authentication and landing preserved
import { useEffect, useMemo, useRef, useState } from "react";
import LandingPage from "./components/LandingPage";
import vestiqWordmark from "./assets/vestiq-wordmark-exact.png";
import authWardrobeBg from "./assets/vestiq-auth-clean-bg.png";
import StylistChat from "./components/StylistChat.jsx";
import vestiqLogoIcon from "./assets/vestiq-logo.png";
import SetPassword from "./components/SetPassword.jsx";
import "./dashboard-theme.css";
import "./vestiq-polish.css";

// Reads the result of the Google/Instagram round-trip once, then cleans the address bar.
// The backend sends the JWT in the URL fragment (#token=...) and errors as ?oauth_error=...
const OAUTH_RETURN = (() => {
  if (typeof window === "undefined") return { token: "", error: "" };
  const hash = new URLSearchParams(window.location.hash.replace(/^#/, ""));
  const query = new URLSearchParams(window.location.search);
  const result = {
    token: hash.get("token") || "",
    error: query.get("oauth_error") || "",
  };
  if (result.token || result.error) {
    window.history.replaceState(null, "", window.location.pathname);
  }
  return result;
})();

const API_URL = "https://vestiq-backend.onrender.com";

const GENDER_OPTIONS = [
  { value: "female", label: "Women's" },
  { value: "male", label: "Men's" },
];

const STYLE_VIBES = ["Minimal", "Street", "Elegant", "Traditional", "Casual", "A bit of everything"];
// Expiry (ms) read from the JWT payload; 0 when the token is unreadable.
function tokenExpiry(token) {
  try {
    const payload = JSON.parse(atob(token.split(".")[1].replace(/-/g, "+").replace(/_/g, "/")));
    return payload.exp ? payload.exp * 1000 : Infinity;
  } catch {
    return 0;
  }
}

// Reads the user id from the JWT payload (no verification - only used to key a per-user, per-day flag).
function tokenUserId(token) {
  try {
    const payload = JSON.parse(atob(token.split(".")[1].replace(/-/g, "+").replace(/_/g, "/")));
    return String(payload.sub || payload.email || payload.user_id || "user");
  } catch {
    return "user";
  }
}

// Saved looks / wear history are stored per account, so one login never sees another login's data.
function userStoreKey(base, token) {
  return `${base}:${tokenUserId(token)}`;
}

// Landing page GitHub card: put your Vestiq repository link here.
const VESTIQ_GITHUB_URL = "https://github.com/";

// Chatbot identity - change it here only.
const CHATBOT_NAME = "MIRA";
const CHATBOT_SUBTITLE = "Your Personal AI Stylist";
const OCCASIONS = ["College", "Office", "Family Events", "Parties", "Weddings", "Everyday", "Travel"];
const CLOTHING_INTERESTS = [
  "Tops", "Shirts", "T-Shirts", "Jeans", "Trousers", "Dresses", "Kurtis",
  "Sarees", "Ethnic Sets", "Skirts", "Jackets", "Co-ords", "Hoodies"
];
const PALETTES = ["Black", "White", "Pastels", "Earthy", "Bright", "Neutrals"];
const MOODS = [
  "Chill", "Cute", "Confident", "Main Character", "Soft",
  "Low-key / Don't talk to me", "Dress to impress", "Keep it simple"
];
const CATEGORY_OPTIONS = [
  "tops", "shirts", "t-shirts", "jeans", "trousers", "dresses", "kurtis",
  "sarees", "ethnic sets", "skirts", "jackets", "co-ords", "hoodies"
];

const GENDER_CATEGORY_OPTIONS = {
  female: [
    "tops", "shirts", "t-shirts", "jeans", "trousers", "dresses", "kurtis",
    "sarees", "ethnic sets", "skirts", "jackets", "co-ords", "hoodies",
    "lehenga", "anarkali", "blouse", "gown", "palazzo", "leggings_salwar",
    "dupatta", "dhoti_pants", "sharara", "gharara"
  ],
  male: [
    "t-shirts", "shirts", "jeans", "pants", "trousers", "shorts", "gym wear",
    "casual wear", "formal wear", "jackets", "hoodies", "sweatshirts",
    "kurta", "kurta_pajama", "ethnic sets", "dhoti", "dhoti_pants",
    "sherwani", "nehru_jacket", "bandhgala"
  ],
};

const REVIEW_CATEGORY_OPTIONS = [
  ...new Set([
    ...GENDER_CATEGORY_OPTIONS.female,
    ...GENDER_CATEGORY_OPTIONS.male,
    "top", "t-shirt", "shirt", "dress", "skirt", "jacket"
  ])
];

const DOMAIN_OPTIONS = ["western", "traditional", "indo_western", "fusion", "other"];
// Labels for the canonical domain values. Values must match the backend (ALLOWED_DOMAINS).
const DOMAIN_LABELS = {
  western: "Western",
  traditional: "Traditional",
  indo_western: "Indo-Western",
  fusion: "Fusion",
  other: "Other",
};
const domainLabel = (value) => DOMAIN_LABELS[value] || displayLabel(value);

const GENDER_NAME_OPTIONS = {
  female: [
    "T-Shirt", "Shirt", "Top", "Jeans", "Trousers", "Dress", "Kurti", "Saree",
    "Ethnic Set", "Skirt", "Jacket", "Co-ord Set", "Hoodie", "Dhoti Pants",
    "Anarkali Suit", "Lehenga", "Palazzo", "Blouse", "Dupatta", "Gown",
    "Salwar Suit", "Sharara", "Gharara", "Other"
  ],
  male: [
    "T-Shirt", "Shirt", "Jeans", "Pants", "Trousers", "Shorts", "Gym Wear",
    "Casual Wear", "Formal Wear", "Jacket", "Hoodie", "Sweatshirt", "Kurta",
    "Kurta Pajama", "Ethnic Set", "Dhoti", "Dhoti Pants", "Sherwani",
    "Nehru Jacket", "Bandhgala", "Other"
  ],
};

const REVIEW_NAME_OPTIONS = [
  ...new Set([...GENDER_NAME_OPTIONS.female, ...GENDER_NAME_OPTIONS.male])
];
const REVIEW_COLOR_OPTIONS = [
  "Black", "White", "Grey", "Beige", "Brown", "Blue", "Navy", "Green",
  "Pink", "Red", "Maroon", "Yellow", "Orange", "Purple", "Pastel",
  "Multicolour", "Metallic", "Neutral", "Other"
];
const REVIEW_STYLE_OPTIONS = [
  "Casual", "Formal", "Party Wear", "Festive", "Ethnic", "Streetwear",
  "Elegant", "Minimal", "Traditional", "Indo-Western", "Boho", "Sporty",
  "Lounge / Comfy", "Other"
];
const REVIEW_OCCASION_OPTIONS = [
  "College", "Office", "Everyday", "Casual Outing", "Party", "Wedding",
  "Festive", "Family Function", "Travel", "Home / Lounge", "Date Night",
  "Workout", "Other"
];

const normalizeOccasionTags = (value) => {
  if (Array.isArray(value)) return value.map((x) => String(x).trim().toLowerCase()).filter(Boolean);
  return String(value || "").split(",").map((x) => x.trim().toLowerCase()).filter(Boolean);
};

const MAX_UPLOAD_SIDE = 1600;

// Shrinks phone photos in the browser before upload, so large or HEIC-derived images
// don't hit request size limits. Falls back to the original file if decoding fails.
async function prepareImageForUpload(file) {
  if (!file || !file.type?.startsWith("image/")) return file;
  try {
    const bitmap = await createImageBitmap(file);
    const scale = Math.min(1, MAX_UPLOAD_SIDE / Math.max(bitmap.width, bitmap.height));
    const canvas = document.createElement("canvas");
    canvas.width = Math.round(bitmap.width * scale);
    canvas.height = Math.round(bitmap.height * scale);
    canvas.getContext("2d").drawImage(bitmap, 0, 0, canvas.width, canvas.height);
    bitmap.close?.();
    const blob = await new Promise((resolve) => canvas.toBlob(resolve, "image/jpeg", 0.85));
    if (!blob) return file;
    const baseName = file.name.replace(/\.[^.]+$/, "") || "clothing";
    return new File([blob], `${baseName}.jpg`, { type: "image/jpeg" });
  } catch {
    return file;
  }
}

const displayLabel = (value) => String(value || "").replaceAll("_", " ").replace(/\b\w/g, (m) => m.toUpperCase());

const emptySetup = {
  name: "",
  gender: "",
  vibes: [],
  occasions: [],
  clothing: [],
  palette: [],
};

function readJSON(key, fallback) {
  try {
    const value = localStorage.getItem(key);
    return value ? JSON.parse(value) : fallback;
  } catch {
    return fallback;
  }
}

// Build the in-app style profile from the database record (the source of truth).
function profileFromUser(user) {
  const saved = user?.style_profile || {};
  return {
    ...emptySetup,
    ...saved,
    name: saved.name || user?.name || "",
    gender: user?.gender || saved.gender || "",
  };
}

function getErrorMessage(data, fallback) {
  if (typeof data?.detail === "string") return data.detail;
  if (Array.isArray(data?.detail)) return data.detail.map((x) => x.msg).join(", ");
  return fallback;
}

// True when a JWT exists and has at least a few seconds of life left.
const isUsableToken = (value) => Boolean(value) && tokenExpiry(value) > Date.now() + 5000;

function App() {
  const [showLanding, setShowLanding] = useState(
    () => !(OAUTH_RETURN.token || OAUTH_RETURN.error)
  );
  const [view, setView] = useState("home");
  const [authMode, setAuthMode] = useState("login");
  const [authStep, setAuthStep] = useState(() =>
    isUsableToken(OAUTH_RETURN.token) ? "ready" : "auth"
  );

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [token, setToken] = useState(() => {
    // A token returned by Google/Instagram login takes priority over the one saved in localStorage.
    if (isUsableToken(OAUTH_RETURN.token)) return OAUTH_RETURN.token;
    // A token left in localStorage may have expired; using it makes every first request fail with 401.
    const saved = localStorage.getItem("vestiq_token") || "";
    if (saved && tokenExpiry(saved) <= Date.now() + 5000) {
      localStorage.removeItem("vestiq_token");
      return "";
    }
    return saved;
  });
  const [displayName, setDisplayName] = useState(() => localStorage.getItem("vestiq_name") || "");
  const [message, setMessage] = useState(() =>
    OAUTH_RETURN.error ? `Google login failed: ${OAUTH_RETURN.error}` : ""
  );
  const [busy, setBusy] = useState(false);
  const [duplicateAccountOpen, setDuplicateAccountOpen] = useState(false);

  const [setupData, setSetupData] = useState(() =>
    readJSON("vestiq_style_profile", emptySetup)
  );
  const [setupStep, setSetupStep] = useState(0);
  const [dailyMood, setDailyMood] = useState(() => {
    const saved = readJSON("vestiq_today_mood", null);
    return saved?.date === new Date().toDateString() ? saved.mood : "";
  });
  const [moodOpen, setMoodOpen] = useState(false);
  const [moodLoading, setMoodLoading] = useState(true);
  const [moodPrompted, setMoodPrompted] = useState(false);

  const [wardrobe, setWardrobe] = useState([]);
  const [recommendations, setRecommendations] = useState([]);
  const [showAllRecommendations, setShowAllRecommendations] = useState(false);
  const [recommendationWeather, setRecommendationWeather] = useState(null);
  const [recommendationLoading, setRecommendationLoading] = useState(false);
  const [recommendationDate, setRecommendationDate] = useState("");
  const [occasion, setOccasion] = useState("College");
  const [stylistPrompt, setStylistPrompt] = useState("");
  const [wardrobeFilter, setWardrobeFilter] = useState("all");
  const [outfitRating, setOutfitRating] = useState({});
  const [savedOutfits, setSavedOutfits] = useState(() => (token ? readJSON(userStoreKey("vestiq_saved_outfits", token), []) : []));
  const [outfitHistory, setOutfitHistory] = useState(() => (token ? readJSON(userStoreKey("vestiq_outfit_history", token), []) : []));
  const storeOwner = useRef(token ? tokenUserId(token) : "");

  const [name, setName] = useState("");
  const [category, setCategory] = useState("");
  const [color, setColor] = useState("");
  const [itemStyle, setItemStyle] = useState("");
  const [itemWeight, setItemWeight] = useState("");
  const [itemOccasions, setItemOccasions] = useState("");
  const [image, setImage] = useState(null);
  const [cameraOpen, setCameraOpen] = useState(false);
  const [cameraLoading, setCameraLoading] = useState(false);
  const videoRef = useRef(null);
  const streamRef = useRef(null);
  const [clothingReviewOpen, setClothingReviewOpen] = useState(false);
  const [clothingReview, setClothingReview] = useState(null);
  const [reviewError, setReviewError] = useState("");
  const submittingRef = useRef(false);

  const nowHour = new Date().getHours();
  const greeting = nowHour >= 5 && nowHour < 12 ? "Good morning" : nowHour < 17 ? "Good afternoon" : nowHour < 21 ? "Good evening" : "Good night";

  const todayLabel = new Date().toLocaleDateString(undefined, {
    weekday: "long", month: "long", day: "numeric"
  });

  const profileGender = setupData.gender || "";
  const visibleCategoryOptions = profileGender ? (GENDER_CATEGORY_OPTIONS[profileGender] || CATEGORY_OPTIONS) : CATEGORY_OPTIONS;
  const visibleReviewCategoryOptions = profileGender ? (GENDER_CATEGORY_OPTIONS[profileGender] || REVIEW_CATEGORY_OPTIONS) : REVIEW_CATEGORY_OPTIONS;
  const visibleReviewNameOptions = profileGender ? (GENDER_NAME_OPTIONS[profileGender] || REVIEW_NAME_OPTIONS) : REVIEW_NAME_OPTIONS;

  const enterApp = () => {
    setShowLanding(false);
    if (token) {
      setAuthStep("ready");
      setView("home");
    } else {
      setAuthStep("auth");
      setView("auth");
    }
  };

  useEffect(() => {
    if (!token) return;
    localStorage.setItem("vestiq_token", token);
  }, [token]);

  useEffect(() => {
    if (displayName) localStorage.setItem("vestiq_name", displayName);
  }, [displayName]);

  useEffect(() => {
    localStorage.setItem("vestiq_style_profile", JSON.stringify(setupData));
  }, [setupData]);

  // Session restore (browser refresh or OAuth return): the database decides whether onboarding is needed.
  useEffect(() => {
    if (!token) return undefined;
    let cancelled = false;
    (async () => {
      try {
        const response = await fetch(`${API_URL}/auth/me`, { headers: { Authorization: `Bearer ${token}` } });
        if (!response.ok || cancelled) return;
        const user = await response.json();
        if (cancelled) return;
        if (user.onboarding_completed) {
          const profile = await fetch(`${API_URL}/auth/style-profile`, { headers: { Authorization: `Bearer ${token}` } })
            .then((r) => (r.ok ? r.json() : null)).catch(() => null);
          if (cancelled) return;
          setSetupData(profileFromUser({ ...user, style_profile: profile?.profile }));
          if (user.name) setDisplayName(user.name);
          setAuthStep((step) => (step === "setup" ? step : "ready"));
        } else {
          setSetupData((current) => ({ ...current, name: current.name || user.name || "", gender: user.gender || current.gender }));
          setAuthStep("setup");
          setView("setup");
        }
      } catch (error) {
        console.error("Unable to verify onboarding status", error);
      }
    })();
    return () => { cancelled = true; };
  }, [token]);

  // Load this account's saved looks / history whenever the logged-in account changes.
  useEffect(() => {
    if (!token) {
      storeOwner.current = "";
      return;
    }
    storeOwner.current = tokenUserId(token);
    setSavedOutfits(readJSON(userStoreKey("vestiq_saved_outfits", token), []));
    setOutfitHistory(readJSON(userStoreKey("vestiq_outfit_history", token), []));
    setOutfitRating({});
  }, [token]);

  useEffect(() => {
    if (!token || storeOwner.current !== tokenUserId(token)) return;
    localStorage.setItem(userStoreKey("vestiq_saved_outfits", token), JSON.stringify(savedOutfits));
  }, [savedOutfits]);

  useEffect(() => {
    if (!token || storeOwner.current !== tokenUserId(token)) return;
    localStorage.setItem(userStoreKey("vestiq_outfit_history", token), JSON.stringify(outfitHistory));
  }, [outfitHistory]);

  // One-time recovery of looks saved before accounts were separated. The old data lived under shared
  // browser keys and is never deleted. An entry is given to the logged-in account only when every
  // clothing piece in it exists in THIS account's wardrobe (checked by item id), so ownership is verified.
  useEffect(() => {
    if (!token || !wardrobe.length || storeOwner.current !== tokenUserId(token)) return;
    const flag = userStoreKey("vestiq_legacy_migrated", token);
    if (localStorage.getItem(flag)) return;
    const ids = new Set(wardrobe.map((item) => String(item.id)));
    const owned = (entry) => {
      const pieces = [entry?.outfit?.top, entry?.outfit?.bottom].filter(Boolean);
      return pieces.length > 0 && pieces.every((piece) => ids.has(String(piece.id)));
    };
    const merge = (current, legacy) => {
      if (!Array.isArray(legacy)) return current;
      const seen = new Set(current.map((entry) => entry.key));
      return [...current, ...legacy.filter((entry) => entry?.key && !seen.has(entry.key) && owned(entry))];
    };
    setSavedOutfits((current) => merge(current, readJSON("vestiq_saved_outfits", [])));
    setOutfitHistory((current) => merge(current, readJSON("vestiq_outfit_history", [])));
    localStorage.setItem(flag, "1");
  }, [token, wardrobe]);

  useEffect(() => {
    if (token) loadWardrobe(true);
  }, [token]);

  const loadTodayMood = async () => {
    if (!token) {
      setMoodLoading(false);
      return;
    }

    setMoodLoading(true);
    try {
      const response = await fetch(`${API_URL}/auth/mood/today`, {
        headers: { Authorization: `Bearer ${token}` },
      });

      if (response.ok) {
        const data = await response.json();
        if (data.mood) {
          setDailyMood(data.mood);
          localStorage.setItem(
            "vestiq_today_mood",
            JSON.stringify({ mood: data.mood, date: new Date().toDateString() })
          );
        } else {
          setDailyMood("");
        }
      }
    } catch (error) {
      console.error("Today's mood load error:", error);
    } finally {
      setMoodLoading(false);
    }
  };

  useEffect(() => {
    if (token) loadTodayMood();
  }, [token]);

  useEffect(() => {
    if (!token || view !== "home" || moodLoading || dailyMood || moodPrompted) return;

    const promptKey = `vestiq_mood_prompt_v2_${tokenUserId(token)}_${new Date().toDateString()}`;
    if (localStorage.getItem(promptKey)) {
      setMoodPrompted(true);
      return;
    }

    const timer = setTimeout(() => {
      localStorage.setItem(promptKey, "1");
      setMoodPrompted(true);
      setMoodOpen(true);
    }, 450);
    return () => clearTimeout(timer);
  }, [token, view, moodLoading, dailyMood, moodPrompted]);

  const [weatherStatus, setWeatherStatus] = useState("idle");
  const [weatherError, setWeatherError] = useState("");

  const loadHomeWeather = async () => {
    if (!token) return;
    setWeatherStatus("loading");
    setWeatherError("");
    try {
      const d = new Date();
      const today = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
      const params = new URLSearchParams({
        city: "Meerut",
        target_date: today,
        occasion: String(occasion || "everyday").toLowerCase(),
      });
      const response = await fetch(`${API_URL}/recommendations?${params.toString()}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      let data = null;
      try { data = await response.json(); } catch { data = null; }
      if (!response.ok) {
        const detail = data?.detail;
        throw new Error(
          detail ? (typeof detail === "string" ? detail : JSON.stringify(detail)) : `Weather request failed (HTTP ${response.status}).`
        );
      }
      if (!data?.weather) throw new Error("The server replied, but sent no weather data.");
      setRecommendationWeather(data.weather);
      setWeatherStatus("ok");
    } catch (error) {
      console.error("Home weather error:", error);
      setWeatherError(
        error instanceof TypeError ? "Can't reach the backend. Is it running?" : error.message || "Weather unavailable."
      );
      setWeatherStatus("error");
    }
  };

  useEffect(() => {
    if (token && view === "home" && !recommendationWeather && weatherStatus === "idle") loadHomeWeather();
  }, [token, view, recommendationWeather, weatherStatus]);

  useEffect(() => () => closeCamera(), []);

  const hasProfile = Boolean(setupData.name || setupData.vibes?.length || setupData.occasions?.length);

  const login = async () => {
    if (!email.trim() || !password.trim()) {
      setMessage("Please enter email and password.");
      return;
    }
    setBusy(true);
    setMessage("");
    try {
      const response = await fetch(`${API_URL}/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: new URLSearchParams({ username: email.trim(), password }),
      });
      const data = await response.json();
      if (!response.ok) {
        setMessage(getErrorMessage(data, "Login failed."));
        return;
      }
      setToken(data.access_token);
      const user = data.user || {};
      const onboardingDone = Boolean(user.onboarding_completed);
      if (onboardingDone) {
        const profile = await fetch(`${API_URL}/auth/style-profile`, { headers: { Authorization: `Bearer ${data.access_token}` } })
          .then((r) => (r.ok ? r.json() : null)).catch(() => null);
        setSetupData(profileFromUser({ ...user, style_profile: profile?.profile }));
      } else {
        setSetupData((current) => ({ ...emptySetup, ...current, name: current.name || user.name || "", gender: user.gender || "" }));
        setSetupStep(0);
      }
      if (user.name) setDisplayName(user.name);
      setMessage("Login successful.");
      setAuthStep(onboardingDone ? "ready" : "setup");
      setView(onboardingDone ? "home" : "setup");
    } catch (error) {
      console.error(error);
      setMessage("Unable to connect to backend.");
    } finally {
      setBusy(false);
    }
  };

  const register = async () => {
    if (!displayName.trim() || !email.trim() || !password || !confirmPassword) {
      setMessage("Please complete all account fields.");
      return;
    }
    if (password.length < 6) {
      setMessage("Password should contain at least 6 characters.");
      return;
    }
    if (password !== confirmPassword) {
      setMessage("Passwords do not match.");
      return;
    }
    setBusy(true);
    setMessage("");
    try {
      const response = await fetch(`${API_URL}/auth/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name: displayName.trim(), email: email.trim(), password }),
      });
      const data = await response.json();
      if (!response.ok) {
        const detail = getErrorMessage(data, "Unable to create account.");
        if (response.status === 400 && detail.toLowerCase().includes("already registered")) {
          setDuplicateAccountOpen(true);
          setMessage("");
        } else {
          setMessage(detail);
        }
        return;
      }
      localStorage.setItem(`vestiq_name_${email.trim().toLowerCase()}`, displayName.trim());
      const loginResponse = await fetch(`${API_URL}/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: new URLSearchParams({ username: email.trim(), password }),
      });
      const loginData = await loginResponse.json();
      if (!loginResponse.ok) {
        setMessage("Account created. Please log in to continue.");
        setAuthMode("login");
        return;
      }
      setToken(loginData.access_token);
      setMessage("Account created. Let's set up your style.");
      setAuthStep("setup");
      setView("setup");
      setSetupStep(0);
      setSetupData((current) => ({ ...current, name: displayName.trim() }));
      localStorage.setItem(`vestiq_name_${email.trim().toLowerCase()}`, displayName.trim());
    } catch (error) {
      console.error(error);
      setMessage("Unable to connect to backend.");
    } finally {
      setBusy(false);
    }
  };

  const socialLogin = (provider) => {
    // OAuth must be handled by the backend so provider secrets never live in the frontend.
    // The backend route should redirect the browser to Google/Facebook and then back to Vestiq.
    const providerName = provider === "google" ? "Google" : "Facebook";
    setMessage(`Connecting to ${providerName}…`);
    window.location.assign(`${API_URL}/auth/${provider}`);
  };

  const completeSetup = async () => {
    const profile = { ...setupData, name: setupData.name || displayName || "Vestiq user" };
    if (!profile.gender) {
      setMessage("Please choose Women's or Men's wardrobe first.");
      return;
    }

    if (!token) {
      setMessage("Please log in again to save your profile.");
      return;
    }

    setBusy(true);
    try {
      const headers = { "Content-Type": "application/json", Authorization: `Bearer ${token}` };

      // 1) Existing endpoint: wardrobe gender (unchanged behaviour).
      const response = await fetch(`${API_URL}/auth/profile`, {
        method: "PATCH",
        headers,
        body: JSON.stringify({
          gender: profile.gender,
          clothing_preference: "both",
          preferred_styles: [],
          preferred_traditional_categories: [],
        }),
      });
      if (!response.ok) {
        const data = await response.json().catch(() => ({}));
        setMessage(getErrorMessage(data, "Unable to save your wardrobe preference."));
        return;
      }

      // 2) Existing endpoint: name, vibes, occasions, clothing, palette. The server marks
      //    onboarding_completed = true only after this write succeeds.
      const styleResponse = await fetch(`${API_URL}/auth/style-profile`, {
        method: "PUT",
        headers,
        body: JSON.stringify({
          name: profile.name,
          vibes: profile.vibes || [],
          occasions: profile.occasions || [],
          clothing: profile.clothing || [],
          palette: profile.palette || [],
        }),
      });
      if (!styleResponse.ok) {
        const data = await styleResponse.json().catch(() => ({}));
        setMessage(getErrorMessage(data, "Unable to save your style profile."));
        return;
      }

      setSetupData(profile);
      setDisplayName(profile.name);
      setAuthStep("ready");
      setView("home");
      setMessage("Your Vestiq style profile is ready.");
    } catch (error) {
      console.error(error);
      setMessage("Unable to save your wardrobe preference.");
    } finally {
      setBusy(false);
    }
  };

  const toggleSetupValue = (field, value) => {
    setSetupData((current) => {
      const values = current[field] || [];
      return {
        ...current,
        [field]: values.includes(value) ? values.filter((x) => x !== value) : [...values, value],
      };
    });
  };

  const saveMood = async (mood) => {
    setDailyMood(mood);
    localStorage.setItem(
      "vestiq_today_mood",
      JSON.stringify({ mood, date: new Date().toDateString() })
    );
    setMoodOpen(false);
    setMoodPrompted(true);
    setMessage(`Today's vibe: ${mood}. Your fit just got a little easier ✦`);

    if (!token) return;

    try {
      const response = await fetch(`${API_URL}/auth/mood`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ mood }),
      });

      if (!response.ok) {
        const data = await response.json().catch(() => ({}));
        setMessage(data.detail || "Mood saved locally, but could not sync to your Vestiq profile.");
      }
    } catch (error) {
      console.error("Mood save error:", error);
      setMessage("Mood saved locally. Vestiq will keep your choice.");
    }
  };

  const logout = () => {
    closeCamera();
    localStorage.removeItem("vestiq_token");
    localStorage.removeItem("vestiq_today_mood");
    setDailyMood("");
    setMoodPrompted(false);
    setMoodOpen(false);
    setRecommendationWeather(null);
    setWeatherStatus("idle");
    setWeatherError("");
    setSavedOutfits([]);
    setOutfitHistory([]);
    setOutfitRating({});
    setRecommendations([]);
    setWardrobe([]);
    setSetupData(emptySetup);
    setToken("");
    setView("auth");
    setAuthStep("auth");
    setMessage("");
  };

  // Sign out cleanly when the session expires while the app is open.
  useEffect(() => {
    if (!token) return undefined;
    const msLeft = tokenExpiry(token) - Date.now();
    if (!Number.isFinite(msLeft)) return undefined;
    const timer = setTimeout(() => {
      logout();
      setMessage("Session expired. Please log in again.");
    }, Math.max(msLeft, 0));
    return () => clearTimeout(timer);
  }, [token]);

  async function loadWardrobe(silent = false) {
    if (!token) return;
    try {
      const response = await fetch(`${API_URL}/wardrobe/items`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      const data = await response.json();
      if (!response.ok) {
        if (!silent) setMessage(data.detail || "Unable to load wardrobe.");
        return;
      }
      setWardrobe(Array.isArray(data) ? data : []);
      if (!silent) setMessage("Wardrobe loaded.");
    } catch (error) {
      console.error(error);
      if (!silent) setMessage("Unable to connect to backend.");
    }
  }

  const uploadClothing = async () => {
    if (!token) return setMessage("Please login first.");
    if (!image) return setMessage("Please select or capture an image.");

    // No AI classification here. The user chooses every clothing detail manually.
    const previewUrl = URL.createObjectURL(image);
    setClothingReview({
      image_url: previewUrl,
      image_file: image,
      name: "",
      domain: "",
      category: "",
      color: "",
      style: "",
      outfit_weight: "",
      occasion_tags: [],
      custom_name: "",
      custom_category: "",
      custom_color: "",
      custom_style: "",
      custom_occasion: "",
    });
    setClothingReviewOpen(true);
    setReviewError("");
    setMessage("Choose the details for this clothing item before saving.");
  };

  const updateClothingReview = (field, value) => {
    setClothingReview((current) => ({ ...(current || {}), [field]: value }));
  };

  const confirmClothingReview = async () => {
    if (submittingRef.current || !token || !clothingReview) return;
    const finalName = (clothingReview.name === "__other__" ? clothingReview.custom_name : clothingReview.name || "").trim();
    const finalDomain = (clothingReview.domain || "").trim();
    const finalCategory = (clothingReview.category === "__other__" ? clothingReview.custom_category : clothingReview.category || "").trim();
    const finalColor = (clothingReview.color === "__other__" ? clothingReview.custom_color : clothingReview.color || "").trim();
    const finalStyle = (clothingReview.style === "__other__" ? clothingReview.custom_style : clothingReview.style || "").trim();
    const finalOccasions = normalizeOccasionTags(clothingReview.occasion_tags).map((x) => x === "__other__" ? String(clothingReview.custom_occasion || "").trim().toLowerCase() : x).filter(Boolean);

    if (!finalName) return setReviewError("Please enter a clothing name.");
    if (!finalDomain) return setReviewError("Please choose or enter a clothing domain.");
    if (!finalCategory) return setReviewError("Please choose or enter a clothing category.");
    if (!finalColor) return setReviewError("Please choose or enter the clothing colour.");
    if (!finalOccasions.length) return setReviewError("Please choose at least one occasion.");

    submittingRef.current = true;
    setBusy(true);
    setReviewError("");
    try {
      const imageFile = await prepareImageForUpload(clothingReview.image_file || image);

      const formData = new FormData();
      formData.append("name", finalName);
      formData.append("domain", finalDomain.toLowerCase());
      formData.append("category", finalCategory.toLowerCase());
      formData.append("color", finalColor.toLowerCase());
      formData.append("style", finalStyle.toLowerCase());
      formData.append("outfit_weight", clothingReview.outfit_weight || "");
      formData.append("occasion_tags", finalOccasions.join(", "));
      formData.append("image", imageFile);

      // No Content-Type header: the browser sets the multipart boundary itself.
      const response = await fetch(`${API_URL}/wardrobe/items`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
        body: formData,
      });

      // Read as text first, so an HTML error page from a proxy doesn't break parsing.
      const raw = await response.text();
      let data = {};
      try { data = raw ? JSON.parse(raw) : {}; } catch { data = {}; }

      if (!response.ok) {
        const fallback = response.status === 413
          ? "That photo is too large. Try a smaller image."
          : `Could not save this item (HTTP ${response.status}). Please try again.`;
        setReviewError(getErrorMessage(data, fallback));
        return;
      }

      if (clothingReview?.image_url?.startsWith("blob:")) {
        URL.revokeObjectURL(clothingReview.image_url);
      }
      setClothingReviewOpen(false);
      setClothingReview(null);
      setName("");
      setCategory("");
      setColor("");
      setItemStyle("");
      setItemWeight("");
      setItemOccasions("");
      setImage(null);
      const fileInput = document.getElementById("clothing-file");
      if (fileInput) fileInput.value = "";
      setMessage(`${data.name || "Clothing item"} added to your wardrobe.`);
      await loadWardrobe(true);
    } catch (error) {
      console.error(error);
      setReviewError("Network error while saving. Check your connection and try again.");
    } finally {
      submittingRef.current = false;
      setBusy(false);
    }
  };

  const cancelClothingReview = () => {
    if (clothingReview?.image_url?.startsWith("blob:")) {
      URL.revokeObjectURL(clothingReview.image_url);
    }
    setClothingReviewOpen(false);
    setClothingReview(null);
    setMessage("Review cancelled. Your clothing has not been added to the wardrobe.");
  };

  const openCamera = async () => {
    try {
      setCameraLoading(true);
      const stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: "environment" }, audio: false });
      streamRef.current = stream;
      setCameraOpen(true);
      setTimeout(() => {
        if (videoRef.current) {
          videoRef.current.srcObject = stream;
          videoRef.current.play();
        }
      }, 100);
    } catch (error) {
      console.error(error);
      setMessage("Unable to access camera. Please allow camera permission.");
    } finally {
      setCameraLoading(false);
    }
  };

  const closeCamera = () => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    }
    if (videoRef.current) videoRef.current.srcObject = null;
    setCameraOpen(false);
  };

  const capturePhoto = () => {
    if (!videoRef.current) return;
    const video = videoRef.current;
    const canvas = document.createElement("canvas");
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    const context = canvas.getContext("2d");
    context.drawImage(video, 0, 0, canvas.width, canvas.height);
    canvas.toBlob((blob) => {
      if (!blob) return setMessage("Unable to capture image.");
      setImage(new File([blob], `vestiq-camera-${Date.now()}.jpg`, { type: "image/jpeg" }));
      setMessage("Photo captured. Ready to upload.");
      closeCamera();
    }, "image/jpeg", 0.9);
  };

  const markAsWorn = async (itemId) => {
    if (!token) return setMessage("Please login first.");
    try {
      const response = await fetch(`${API_URL}/wardrobe/items/${itemId}/worn`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
      });
      const data = await response.json();
      if (!response.ok) return setMessage(data.detail || "Unable to update wear history.");
      setMessage("Clothing marked as worn today.");
      await loadWardrobe(true);
    } catch (error) {
      console.error(error);
      setMessage("Unable to connect to backend.");
    }
  };

  const undoWorn = async (itemId) => {
    if (!token) return setMessage("Please login first.");
    try {
      const response = await fetch(`${API_URL}/wardrobe/items/${itemId}/unworn`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
      });
      const data = await response.json();
      if (!response.ok) return setMessage(data.detail || "Unable to undo wear status.");
      setMessage("Worn status removed.");
      await loadWardrobe(true);
    } catch (error) {
      console.error(error);
      setMessage("Unable to connect to backend.");
    }
  };

  const deleteClothing = async (itemId, itemName) => {
    if (!token) return setMessage("Please login first.");
    const confirmed = window.confirm(`Delete ${itemName || "this clothing item"} from your wardrobe?`);
    if (!confirmed) return;
    try {
      const response = await fetch(`${API_URL}/wardrobe/items/${itemId}`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}` },
      });
      const data = await response.json();
      if (!response.ok) return setMessage(data.detail || "Unable to delete clothing item.");
      setMessage(`${itemName || "Clothing item"} deleted from your wardrobe.`);
      await loadWardrobe(true);
    } catch (error) {
      console.error(error);
      setMessage("Unable to connect to backend.");
    }
  };

  
const parseStylistPrompt = (prompt) => {
  const text = String(prompt || "").toLowerCase();

  const colors = [
    "pink", "black", "white", "blue", "navy", "red",
    "green", "purple", "yellow", "orange", "brown",
    "beige", "cream", "grey", "gray", "maroon", "pastel"
  ];

  const styles = [
    "elegant", "modern", "traditional", "minimal",
    "bold", "classic", "trendy", "street", "casual",
    "formal", "festive", "ethnic", "indo-western"
  ];

  const topTypes = [
    "t-shirt", "tshirt", "t-shirts", "shirt", "shirts",
    "top", "tops", "kurti", "blouse", "hoodie",
    "sweater", "jacket"
  ];

  const bottomTypes = [
    "wide-leg jeans", "wide leg jeans", "straight-fit jeans",
    "straight fit jeans", "bell-bottom", "flared jeans",
    "baggy jeans", "jeans", "trousers", "pants",
    "palazzo", "skirt", "shorts"
  ];

  const onePieceTypes = [
    "one-piece", "one piece", "dress", "gown",
    "saree", "anarkali"
  ];

  const findMentioned = (values) =>
    values.find((value) => text.includes(value)) || "";

  const colorPattern =
    "pink|black|white|blue|navy|red|green|purple|yellow|orange|brown|beige|cream|grey|gray|maroon|pastel";

  const topPattern =
    "t-shirt|tshirt|shirt|top|kurti|blouse|hoodie|sweater|jacket";

  const bottomPattern =
    "wide[- ]leg jeans|straight[- ]fit jeans|bell-bottom|flared jeans|baggy jeans|jeans|trousers|pants|palazzo|skirt|shorts";

  const findSlotColor = (garments) => {
    const regex = new RegExp(
      `\\b(${colorPattern})\\b\\s+(?:\\w+\\s+){0,2}(?:${garments})\\b|\\b(?:${garments})\\b\\s+(?:in\\s+|of\\s+|colour\\s+|color\\s+)?(${colorPattern})\\b`,
      "i"
    );

    const match = text.match(regex);
    return (match?.[1] || match?.[2] || "").toLowerCase();
  };

  const topType = findMentioned(topTypes);
  const bottomType = findMentioned(bottomTypes);
  const onePiece = onePieceTypes.some((value) =>
    text.includes(value)
  ) || /no bottom\s*\/?\s*one-piece/i.test(text);

  const topColor = findSlotColor(topPattern);
  const bottomColor = findSlotColor(bottomPattern);

  const colorMatches = colors.filter((value) =>
    new RegExp(`\\b${value}\\b`, "i").test(text)
  );

  const explicitNoPreference =
    text.includes("no preference") ||
    text.includes("anything");

  return {
    style: findMentioned(styles) ||
      (!explicitNoPreference
        ? setupData.vibes?.[0]?.toLowerCase() || ""
        : ""),

    color: colorMatches[0] || "",

    topColor: topColor ||
      (topType && colorMatches.length ? colorMatches[0] : ""),

    bottomColor,

    topType,
    bottomType: onePiece ? "" : bottomType,
    onePiece,

    weight: ["light", "medium", "heavy"].find((value) =>
      text.includes(value)
    ) || ""
  };
};

const getRecommendations = async (
  targetOccasion = occasion,
  promptOverride = null
) => {
  if (!token) {
    setMessage("Please login first.");
    return;
  }

  setRecommendationLoading(true);
  setMessage("");

  try {
    const targetDate =
      recommendationDate ||
      new Date(Date.now() + 86400000)
        .toISOString()
        .split("T")[0];

    const activePrompt =
      promptOverride !== null ? promptOverride : stylistPrompt;

    const detected = parseStylistPrompt(activePrompt);

    const params = new URLSearchParams({
      city: "Meerut",
      target_date: targetDate,
      occasion: String(targetOccasion).toLowerCase()
    });

    if (detected.style) {
      params.set("style", detected.style);
    }

    if (detected.color) {
      params.set("preferred_color", detected.color);
    }

    if (detected.topColor) {
      params.set("top_color", detected.topColor);
    }

    if (detected.bottomColor) {
      params.set("bottom_color", detected.bottomColor);
    }

    if (detected.topType) {
      params.set("top_type", detected.topType);
    }

    if (detected.bottomType) {
      params.set("bottom_type", detected.bottomType);
    }

    if (detected.onePiece) {
      params.set("one_piece", "true");
    }

    if (detected.weight) {
      params.set("outfit_weight", detected.weight);
    }

    if (dailyMood) {
      params.set("mood", dailyMood);
    }

    if (activePrompt.trim()) {
      params.set("specific_request", activePrompt.trim());
      params.set("request", activePrompt.trim());
    }

    const response = await fetch(
      `${API_URL}/recommendations?${params.toString()}`,
      {
        headers: {
          Authorization: `Bearer ${token}`
        }
      }
    );

    const data = await response.json();

    if (!response.ok) {
      setRecommendations([]);
      setMessage(
        data.detail || "Unable to get recommendations."
      );
      return;
    }

    const results = Array.isArray(data.recommendations)
      ? data.recommendations
      : [];

    setRecommendations(results);
    setRecommendationWeather(data.weather || null);

    setMessage(
      results.length
        ? "Your outfit recommendations are ready."
        : "No matching outfits were found. Try changing your preferences or adding more clothes to your wardrobe."
    );
  } catch (error) {
    console.error("Recommendation error:", error);
    setMessage("Unable to connect to backend.");
  } finally {
    setRecommendationLoading(false);
  }
};


  const outfitKey = (outfit) => `${outfit?.top?.id || "none"}-${outfit?.bottom?.id || "none"}`;

  const saveOutfit = (outfit) => {
    const key = outfitKey(outfit);
    setSavedOutfits((current) => current.some((x) => x.key === key) ? current : [
      ...current,
      { key, outfit, savedAt: new Date().toISOString() }
    ]);
    setMessage("Outfit saved to your collection.");
  };

  const removeSavedOutfit = (outfit) => {
    const key = outfitKey(outfit);
    setSavedOutfits((current) => current.filter((x) => x.key !== key));
    setMessage("Removed from your saved looks.");
  };

  const rateOutfit = (outfit, rating) => {
    setOutfitRating((current) => ({ ...current, [outfitKey(outfit)]: rating }));
    setMessage(`Rated this outfit ${rating}/5.`);
  };

  const wearOutfit = async (outfit) => {
    const ids = [outfit?.top?.id, outfit?.bottom?.id].filter(Boolean);
    for (const id of ids) await markAsWorn(id);
    const historyEntry = {
      key: `${outfitKey(outfit)}-${Date.now()}`,
      outfit,
      mood: dailyMood,
      occasion,
      wornAt: new Date().toISOString(),
    };
    setOutfitHistory((current) => [historyEntry, ...current].slice(0, 50));
    setMessage("Outfit marked as worn and added to your history.");
  };

  const filteredWardrobe = useMemo(() => {
    if (wardrobeFilter === "all") return wardrobe;
    return wardrobe.filter((item) => String(item.category || "").toLowerCase() === wardrobeFilter.toLowerCase());
  }, [wardrobe, wardrobeFilter]);

  if (showLanding) {
    return (
      <>
        <LandingPage onEnter={enterApp} />
      </>
    );
  }

  if (view === "auth" || authStep === "auth") {
    return (
      <AuthPage
        mode={authMode}
        setMode={(mode) => { setAuthMode(mode); setMessage(""); }}
        email={email}
        setEmail={setEmail}
        password={password}
        setPassword={setPassword}
        confirmPassword={confirmPassword}
        setConfirmPassword={setConfirmPassword}
        name={displayName}
        setName={setDisplayName}
        busy={busy}
        message={message}
        onSubmit={authMode === "login" ? login : register}
        onSocialLogin={socialLogin}
        onBack={() => setShowLanding(true)}
        duplicateAccountOpen={duplicateAccountOpen}
        onCloseDuplicateAccount={() => setDuplicateAccountOpen(false)}
      />
    );
  }

  if (view === "setup") {
    return (
      <SetupFlow
        setupData={setupData}
        setupStep={setupStep}
        setSetupStep={setSetupStep}
        toggleSetupValue={toggleSetupValue}
        completeSetup={completeSetup}
        setSetupData={setSetupData}
        displayName={displayName}
        message={message}
      />
    );
  }

  return (
    <div className="min-vh-100 bg-light vestiq-app">
      <AppNav
        view={view}
        setView={setView}
        displayName={displayName || setupData.name || "Vestiq user"}
        dailyMood={dailyMood}
        onMood={() => setMoodOpen(true)}
        onLogout={logout}
      />

      <main className={`container py-4 vq-view vq-view-${view}`}>
        {message && <div className="alert alert-secondary py-2">{message}</div>}

        {view === "home" && (
          <Dashboard
            name={displayName || setupData.name || "there"}
            todayLabel={todayLabel}
            greeting={greeting}
            dailyMood={dailyMood}
            wardrobe={wardrobe}
            recommendations={recommendations}
            weather={recommendationWeather}
            weatherStatus={weatherStatus}
            weatherError={weatherError}
            onRetryWeather={loadHomeWeather}
            onStyleMe={() => { setView("style"); getRecommendations(); }}
            onWardrobe={() => setView("wardrobe")}
            onMood={() => setMoodOpen(true)}
            onRefreshWardrobe={() => loadWardrobe(false)}
          />
        )}

        {view === "wardrobe" && (
          <WardrobeView
            wardrobe={filteredWardrobe}
            filter={wardrobeFilter}
            setFilter={setWardrobeFilter}
            categories={visibleCategoryOptions}
            name={name}
            setName={setName}
            category={category}
            setCategory={setCategory}
            color={color}
            setColor={setColor}
            itemStyle={itemStyle}
            setItemStyle={setItemStyle}
            itemWeight={itemWeight}
            setItemWeight={setItemWeight}
            itemOccasions={itemOccasions}
            setItemOccasions={setItemOccasions}
            image={image}
            setImage={setImage}
            cameraOpen={cameraOpen}
            cameraLoading={cameraLoading}
            videoRef={videoRef}
            openCamera={openCamera}
            closeCamera={closeCamera}
            capturePhoto={capturePhoto}
            uploadClothing={uploadClothing}
            busy={busy}
            onRefresh={() => loadWardrobe(false)}
            markAsWorn={markAsWorn}
            undoWorn={undoWorn}
            deleteClothing={deleteClothing}
          />
        )}

        {view === "style" && (
          <StyleView
            dailyMood={dailyMood}
            onMood={() => setMoodOpen(true)}
            occasion={occasion}
            setOccasion={setOccasion}
            recommendationDate={recommendationDate}
            setRecommendationDate={setRecommendationDate}
            stylistPrompt={stylistPrompt}
            setStylistPrompt={setStylistPrompt}
            onGenerate={getRecommendations}
            loading={recommendationLoading}
            weather={recommendationWeather}
            recommendations={recommendations}
            saveOutfit={saveOutfit}
            wearOutfit={wearOutfit}
            rateOutfit={rateOutfit}
            ratings={outfitRating}
          />
        )}

        {view === "stylist" && (
  <StylistChat
    apiUrl={API_URL}
    token={token}
    onOpenStyleMe={() => setView("style")}
  />
)}

        {view === "outfits" && (
          <OutfitsView
            recommendations={recommendations}
            savedOutfits={savedOutfits}
            removeSavedOutfit={removeSavedOutfit}
            history={outfitHistory}
            saveOutfit={saveOutfit}
            wearOutfit={wearOutfit}
            rateOutfit={rateOutfit}
            ratings={outfitRating}
          />
        )}

                {view === "profile" && (
          <>
            <ProfileView
              displayName={displayName}
              setupData={setupData}
              setSetupData={setSetupData}
              onReopenSetup={() => { setSetupStep(0); setView("setup"); }}
              dailyMood={dailyMood}
              onMood={() => setMoodOpen(true)}
              history={outfitHistory}
              saved={savedOutfits}
            />
            <SetPassword apiUrl={API_URL} token={token} />
          </>
        )}
      </main>

      {token && <StyleBuddyLauncher visible={view === "style"} apiUrl={API_URL} token={token} userName={displayName || setupData.name} />}

      {moodOpen && <MoodModal current={dailyMood} onSelect={saveMood} onClose={() => setMoodOpen(false)} />}
      {clothingReviewOpen && <ClothingReviewModal review={clothingReview} nameOptions={visibleReviewNameOptions} categoryOptions={visibleReviewCategoryOptions} onChange={updateClothingReview} onConfirm={confirmClothingReview} onCancel={cancelClothingReview} busy={busy} error={reviewError} />}
    </div>
  );
}

function AuthPage({ mode, setMode, email, setEmail, password, setPassword, confirmPassword, setConfirmPassword, name, setName, busy, message, onSubmit, onSocialLogin, onBack, duplicateAccountOpen, onCloseDuplicateAccount }) {
  const [showPassword, setShowPassword] = useState(false);

  const slogans = mode === "login"
    ? ["Your closet called. It wants better outfits.", "Good outfits start with what you already own.", "Pick a vibe. Vestiq handles the rest."]
    : ["Your wardrobe, but make it smarter.", "A little profile. A lot more you.", "Your style era starts here."];
  const [sloganIndex, setSloganIndex] = useState(0);

  useEffect(() => {
    setSloganIndex(0);
    const timer = setInterval(() => setSloganIndex((x) => (x + 1) % slogans.length), 3200);
    return () => clearInterval(timer);
  }, [mode]);

  return (
    <div className="vestiq-auth-screen">
      <style>{`
        .vestiq-auth-screen{min-height:100vh;min-height:100dvh;height:auto;position:relative;overflow-y:auto;display:flex;align-items:flex-start;justify-content:center;padding:72px 32px 32px;box-sizing:border-box;background-image:linear-gradient(rgba(255,244,251,.10),rgba(255,244,251,.10)),linear-gradient(rgba(40,19,48,.10),rgba(40,19,48,.10)),url(${authWardrobeBg});background-size:cover;background-position:center;background-repeat:no-repeat;font-family:Inter,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;color:#2b1930}
        .vestiq-auth-screen:before{content:"";position:absolute;inset:0;background:linear-gradient(115deg,rgba(255,255,255,.38),transparent 42%,rgba(255,255,255,.18));pointer-events:none}
        .auth-back{position:absolute;left:30px;top:24px;border:1px solid rgba(67,38,72,.12);background:rgba(255,255,255,.48);color:#4b3150;border-radius:999px;padding:10px 17px;font-weight:700;cursor:pointer;backdrop-filter:blur(14px);transition:.2s;z-index:3}.auth-back:hover{transform:translateX(-3px);background:rgba(255,255,255,.72)}
        .auth-room{display:none}.auth-closet{position:absolute;left:-4%;top:9%;width:44%;height:79%;border-radius:0 42px 42px 0;background:linear-gradient(90deg,#6b476e,#8f668f 48%,#62405f);box-shadow:inset -18px 0 50px rgba(28,10,31,.3),0 30px 90px rgba(74,37,75,.18)}
        .auth-closet:before{content:"";position:absolute;left:12%;right:9%;top:9%;height:7px;background:#e8b2dc;border-radius:20px;box-shadow:0 150px 0 #e8b2dc,0 300px 0 #e8b2dc;opacity:.78}.auth-rail{position:absolute;left:13%;right:11%;top:13%;height:2px;background:#f5d8ed;box-shadow:0 150px 0 #f5d8ed,0 300px 0 #f5d8ed}
        .auth-clothes{position:absolute;left:15%;top:16%;width:70%;height:65%;display:flex;align-items:flex-start;gap:18px}.auth-clothes span{width:34px;height:155px;border-radius:8px 8px 14px 14px;background:#d8b2d2;box-shadow:inset 0 0 0 2px rgba(255,255,255,.12),0 12px 20px rgba(30,12,32,.12);transform:skew(-4deg);position:relative}.auth-clothes span:before{content:"";position:absolute;left:9px;top:-16px;width:16px;height:19px;border:2px solid #d7b2d5;border-bottom:0;border-radius:12px 12px 0 0}.auth-clothes span:nth-child(2){height:188px;background:#bfa8dc}.auth-clothes span:nth-child(3){height:145px;background:#efd0df}.auth-clothes span:nth-child(4){height:178px;background:#d7c4a9}.auth-clothes span:nth-child(5){height:160px;background:#a990bf}.auth-clothes span:nth-child(6){height:196px;background:#e8b8cf}
        .auth-vanity{position:absolute;left:5%;bottom:7%;width:33%;height:16%;border-radius:28px 28px 8px 8px;background:#d6a9c9;box-shadow:0 30px 50px rgba(55,22,56,.2)}.auth-vanity:before{content:"";position:absolute;left:22%;right:22%;top:-75px;height:95px;border-radius:48px 48px 10px 10px;background:linear-gradient(135deg,#fff7fc,#cba8cf);box-shadow:0 8px 20px rgba(60,29,61,.18)}
        .auth-rack{position:absolute;right:-2%;top:12%;width:34%;height:76%;border-radius:42px 0 0 42px;background:linear-gradient(135deg,#b8a0c9,#8d6c98);box-shadow:inset 20px 0 45px rgba(255,255,255,.14),0 30px 90px rgba(69,39,75,.16)}.auth-rack:before{content:"";position:absolute;left:12%;right:12%;top:17%;height:6px;border-radius:20px;background:#f5d9e9;box-shadow:0 180px 0 #f5d9e9,0 360px 0 #f5d9e9;opacity:.8}.auth-polaroids{position:absolute;right:7%;top:22%;display:flex;flex-direction:column;gap:18px}.auth-polaroids span{width:100px;height:82px;background:#fff9fc;border:6px solid #fff9fc;box-shadow:0 12px 22px rgba(54,27,59,.15);transform:rotate(4deg)}.auth-polaroids span:nth-child(2){transform:rotate(-5deg);margin-left:35px}.auth-polaroids span:before{content:"";display:block;height:100%;background:linear-gradient(135deg,#e7bddb,#b59acb)}
        .auth-card{position:relative;z-index:2;width:min(920px,92vw);min-height:540px;display:grid;grid-template-columns:1.02fr .98fr;border:1px solid rgba(255,255,255,.62);border-radius:34px;overflow:hidden;background:rgba(43,24,48,.18);box-shadow:0 30px 90px rgba(58,29,63,.22);backdrop-filter:blur(18px)}
        .auth-copy{padding:46px 42px;color:white;background:linear-gradient(145deg,rgba(50,26,55,.74),rgba(92,52,98,.50));position:relative}.auth-kicker{font-size:11px;letter-spacing:4px;font-weight:800;color:#e8a8dc;margin-bottom:18px}.auth-copy h1{font-family:Georgia,"Times New Roman",serif;font-weight:500;font-size:clamp(36px,4vw,56px);line-height:.98;margin:0 0 18px;letter-spacing:-2px}.auth-copy h1 em{color:#edafd9;font-style:italic}.auth-copy p{max-width:420px;color:#f0e2ef;font-size:14.5px;line-height:1.6;margin-bottom:24px}.auth-pills{display:flex;flex-wrap:wrap;gap:10px}.auth-pill{border:1px solid rgba(255,255,255,.28);background:rgba(255,255,255,.08);padding:11px 15px;border-radius:999px;color:#fff;font-size:13px;font-weight:700}.auth-quote{position:absolute;left:42px;bottom:28px;color:#f1d9ed;font-size:14px;font-weight:600;letter-spacing:.2px;line-height:1.5;transition:transform .22s ease,font-size .22s ease,font-weight .22s ease,color .22s ease;text-shadow:0 2px 14px rgba(20,7,24,.25)}.auth-quote:hover{transform:translateY(-2px);font-size:15px;font-weight:800;color:#fff2fb}
        .auth-form{background:rgba(255,253,255,.97);padding:38px 40px;display:flex;flex-direction:column;justify-content:center}.auth-brand-logo-text{display:inline-flex;align-items:flex-start;justify-content:center;align-self:center;width:max-content;color:#321b38;font-family:"Playfair Display",Georgia,"Times New Roman",serif;font-size:48px;line-height:.92;letter-spacing:-2.5px;font-weight:800;text-shadow:none;cursor:default;transition:transform .22s ease,text-shadow .22s ease}.auth-brand-logo-text > span{color:#321b38}.auth-brand-logo-text > em{color:#b56fc4;font-style:italic;font-weight:800}.auth-brand-logo-text > i{color:#d46fa8;font-style:normal;font-size:19px;line-height:1;margin-left:2px;vertical-align:top}.auth-brand-logo-text:hover{transform:scale(1.045);text-shadow:0 0 20px rgba(235,188,255,.72),0 3px 12px rgba(55,26,60,.24)}.auth-tagline{text-align:center;color:#8b718c;font-size:12px;font-weight:700;letter-spacing:2.2px;text-transform:uppercase;margin-bottom:20px}.app-wordmark-button{display:flex;align-items:center;background:#321b38!important;border-radius:12px;padding:5px 10px!important;box-shadow:0 8px 18px rgba(50,27,56,.12)}.app-wordmark{display:block;width:108px;height:auto;object-fit:contain}.setup-wordmark{width:112px;background:#321b38;border-radius:12px;padding:5px 10px;box-sizing:content-box}.auth-tabs{display:grid;grid-template-columns:1fr 1fr;background:#f0e5f0;padding:4px;border-radius:999px;margin-bottom:20px}.auth-tab{border:0;background:transparent;border-radius:999px;padding:12px;font-weight:800;color:#7d657f;cursor:pointer}.auth-tab.active{background:#321b38;color:white;box-shadow:0 8px 18px rgba(50,27,56,.18)}.auth-heading{font-family:Georgia,"Times New Roman",serif;font-size:28px;font-weight:500;margin:0 0 8px;color:#2b1930}.auth-subheading{color:#826c83;font-size:14px;line-height:1.5;margin:0 0 20px}.auth-input-wrap{position:relative;margin-bottom:12px}.auth-input{width:100%;box-sizing:border-box;border:1px solid #ead8e9;background:#fff;border-radius:14px;padding:13px 15px 13px 42px;outline:none;color:#2b1930;transition:.2s}.auth-input:focus{border-color:#c58bcf;box-shadow:0 0 0 4px rgba(197,139,207,.12)}.auth-input-icon{position:absolute;left:15px;top:12px;color:#9b7c9c;font-size:15px}.auth-password-toggle{position:absolute;right:10px;top:8px;border:0;background:transparent;color:#8c6d8e;cursor:pointer;padding:7px}.auth-main-button{width:100%;border:0;border-radius:14px;padding:14px;background:linear-gradient(100deg,#e69bd8,#bca3ef);color:#24162a;font-weight:900;cursor:pointer;box-shadow:0 12px 24px rgba(184,142,213,.25);transition:.2s;margin-top:6px}.auth-main-button:hover{transform:translateY(-2px);box-shadow:0 16px 30px rgba(184,142,213,.32)}.auth-main-button:disabled{opacity:.65;cursor:not-allowed;transform:none}.auth-divider{display:flex;align-items:center;gap:12px;color:#a58ba5;font-size:12px;margin:22px 0 14px}.auth-divider:before,.auth-divider:after{content:"";height:1px;background:#eadce9;flex:1}.auth-socials{display:grid;grid-template-columns:1fr;gap:10px}.auth-social{border:1px solid #e4d5e4;background:#fff;border-radius:13px;padding:12px 10px;font-weight:800;color:#49334d;cursor:pointer;transition:.2s;display:flex;align-items:center;justify-content:center;gap:8px}.auth-social:hover{transform:translateY(-1px);background:#fff8ff;box-shadow:0 8px 18px rgba(60,30,64,.08)}.google-logo{width:18px;height:18px;display:block;flex:none}.auth-foot{margin-top:20px;text-align:center;color:#9a849a;font-size:12px;line-height:1.5}.auth-slogan{margin-top:18px;text-align:center;color:#9a779b;font-size:12px;min-height:18px;transition:.25s}.auth-message{margin-top:13px;padding:10px 12px;border-radius:11px;background:#f7edf6;color:#634c66;font-size:12px}.auth-message.success{background:#eaf7ef;color:#2f6d4c}
        .duplicate-overlay{position:fixed;inset:0;z-index:50;display:flex;align-items:center;justify-content:center;padding:24px;background:rgba(40,20,45,.38);backdrop-filter:blur(8px)}.duplicate-modal{width:min(420px,100%);padding:30px 28px 26px;border:1px solid rgba(255,255,255,.72);border-radius:24px;background:rgba(255,250,255,.98);box-shadow:0 24px 70px rgba(45,20,55,.25);text-align:center;color:#38243d}.duplicate-icon{width:44px;height:44px;margin:0 auto 14px;border-radius:50%;display:flex;align-items:center;justify-content:center;background:linear-gradient(135deg,#e6a0d7,#b99cf0);color:#fff;font-size:20px;box-shadow:0 10px 24px rgba(173,111,181,.22)}.duplicate-modal h3{margin:0;font-family:Georgia,serif;font-size:25px;line-height:1.2}.duplicate-modal p{margin:10px auto 20px;max-width:330px;color:#76627b;font-size:13px;line-height:1.6}.duplicate-primary,.duplicate-secondary{width:100%;border-radius:13px;padding:12px 14px;font-weight:800;cursor:pointer}.duplicate-primary{border:0;background:linear-gradient(90deg,#df91d4,#b99aec);color:#24152a;box-shadow:0 10px 24px rgba(169,117,185,.18)}.duplicate-secondary{margin-top:8px;border:1px solid #e3d6e4;background:#fff;color:#6b5570}.duplicate-primary:hover,.duplicate-secondary:hover{transform:translateY(-1px)}
        @media(max-width:900px){.auth-card{grid-template-columns:1fr;max-width:620px}.auth-copy{display:none}.auth-form{padding:42px 30px}.auth-back{left:18px;top:16px}.auth-closet,.auth-rack{opacity:.45}.auth-socials{grid-template-columns:1fr}}
        @media(max-width:520px){.vestiq-auth-screen{padding:64px 18px 24px}.auth-form{padding:34px 20px}.auth-card{border-radius:24px}.auth-heading{font-size:28px}}
      `}</style>

      <button className="auth-back" onClick={onBack}>← Back to Vestiq</button>

      <div className="auth-card">
        <section className="auth-copy">
          <div className="auth-kicker">WELCOME BACK</div>
          <h1>Your style is<br/>waiting<br/><em>for you.</em> ♡</h1>
          <p>{mode === "login" ? "Log in and let Vestiq turn what you already own into looks that actually feel like you." : "Create your account and let Vestiq learn the little details that make your style yours."}</p>
          <div className="auth-pills"><span className="auth-pill">♧ Personal style</span><span className="auth-pill">▦ Your wardrobe</span><span className="auth-pill">✦ Smart looks</span></div>
          <div className="auth-quote">No boring setup. Just your clothes, your vibe & a little personality.</div>
        </section>

        <section className="auth-form">
          <div className="auth-brand-logo-text" aria-label="Vestiq"><span>vesti</span><em>Q</em><i>✿</i></div>
          <div className="auth-tagline">YOUR STYLE · SIMPLIFIED.</div>

          <div className="auth-tabs">
            <button className={`auth-tab ${mode === "login" ? "active" : ""}`} onClick={() => setMode("login")}>Login</button>
            <button className={`auth-tab ${mode === "register" ? "active" : ""}`} onClick={() => setMode("register")}>Create account</button>
          </div>

          <h2 className="auth-heading">{mode === "login" ? "Welcome back." : "Let’s make your style yours."}</h2>
          <p className="auth-subheading">{mode === "login" ? "Enter your account to continue." : "Create an account, then we’ll build your style profile together."}</p>

          {mode === "register" && <div className="auth-input-wrap"><span className="auth-input-icon">♡</span><input className="auth-input" placeholder="What should we call you?" value={name} onChange={(e) => setName(e.target.value)} /></div>}
          <div className="auth-input-wrap"><span className="auth-input-icon">✉</span><input type="email" className="auth-input" placeholder="Email address" value={email} onChange={(e) => setEmail(e.target.value)} autoComplete="email" /></div>
          <div className="auth-input-wrap"><span className="auth-input-icon">⌑</span><input type={showPassword ? "text" : "password"} className="auth-input" style={{paddingRight:48}} placeholder="Password" value={password} onChange={(e) => setPassword(e.target.value)} autoComplete={mode === "login" ? "current-password" : "new-password"} /><button className="auth-password-toggle" type="button" onClick={() => setShowPassword((x) => !x)}>{showPassword ? "Hide" : "Show"}</button></div>
          {mode === "register" && <div className="auth-input-wrap"><span className="auth-input-icon">✓</span><input type="password" className="auth-input" placeholder="Confirm password" value={confirmPassword} onChange={(e) => setConfirmPassword(e.target.value)} autoComplete="new-password" /></div>}

          <button className="auth-main-button" disabled={busy} onClick={onSubmit}>{busy ? "One sec…" : mode === "login" ? "Enter Vestiq →" : "Create my account →"}</button>

          <div className="auth-divider"><span>or continue with</span></div>
          <div className="auth-socials">
            <button className="auth-social" disabled={busy} onClick={() => onSocialLogin("google")}>
              <svg className="google-logo" viewBox="0 0 24 24" aria-hidden="true">
                <path fill="#4285F4" d="M21.35 12.27c0-.72-.06-1.42-.18-2.09H12v3.96h5.23a4.47 4.47 0 0 1-1.94 2.94v2.45h3.14c1.84-1.69 2.92-4.18 2.92-7.26Z"/>
                <path fill="#34A853" d="M12 21.73c2.63 0 4.84-.87 6.45-2.35l-3.14-2.45c-.87.58-1.98.93-3.31.93-2.54 0-4.7-1.72-5.47-4.03H3.28v2.53A9.74 9.74 0 0 0 12 21.73Z"/>
                <path fill="#FBBC05" d="M6.53 13.83A5.85 5.85 0 0 1 6.22 12c0-.64.11-1.26.31-1.83V7.64H3.28A9.74 9.74 0 0 0 2.27 12c0 1.57.38 3.05 1.01 4.36l3.25-2.53Z"/>
                <path fill="#EA4335" d="M12 6.14c1.43 0 2.71.49 3.72 1.45l2.79-2.79C16.84 3.24 14.63 2.27 12 2.27a9.74 9.74 0 0 0-8.72 5.37l3.25 2.53C7.3 7.86 9.46 6.14 12 6.14Z"/>
              </svg>
              <span>Continue with Google</span>
            </button>
          </div>

          <div className="auth-slogan">{slogans[sloganIndex]}</div>
          {message && <div className={`auth-message ${message.toLowerCase().includes("successful") ? "success" : ""}`}>{message}</div>}
          <div className="auth-foot">By continuing, you’re keeping your wardrobe in one place — and your style a little more you.</div>
        </section>
      </div>

      {duplicateAccountOpen && (
        <div className="duplicate-overlay" role="dialog" aria-modal="true" aria-labelledby="duplicate-title">
          <div className="duplicate-modal">
            <div className="duplicate-icon">✦</div>
            <h3 id="duplicate-title">You already have a Vestiq account.</h3>
            <p>This email is already registered. Log in to continue with your existing wardrobe and style profile.</p>
            <button className="duplicate-primary" onClick={() => { onCloseDuplicateAccount(); setMode("login"); }}>Go to Login →</button>
            <button className="duplicate-secondary" onClick={onCloseDuplicateAccount}>Stay here</button>
          </div>
        </div>
      )}
    </div>
  );
}

function SetupFlow({ setupData, setupStep, setSetupStep, toggleSetupValue, completeSetup, setSetupData, displayName, message }) {
  const clothingOptions = setupData.gender
    ? (GENDER_CATEGORY_OPTIONS[setupData.gender] || CLOTHING_INTERESTS.map((x) => x.toLowerCase()))
    : CLOTHING_INTERESTS.map((x) => x.toLowerCase());
  const steps = [
    { title: "Who are you styling for?", field: "gender", options: GENDER_OPTIONS, single: true },
    { title: "What's your style vibe?", field: "vibes", options: STYLE_VIBES },
    { title: "Where do you usually dress for?", field: "occasions", options: OCCASIONS },
    { title: "What's actually in your wardrobe?", field: "clothing", options: clothingOptions },
    { title: "Which colours feel like you?", field: "palette", options: PALETTES },
  ];
  const step = steps[setupStep];
  const isLast = setupStep === steps.length - 1;
  return (
    <div className="vq-setup">
      <div className="vq-setup-inner">
        <div className="vq-setup-top">
          <span className="vq-setup-wordmark" aria-label="Vestiq">vesti<span>Q</span><i>✿</i></span><span className="vq-setup-count">Style setup {setupStep + 1}/{steps.length}</span>
        </div>
        <div className="vq-setup-progress"><div className="vq-setup-bar" style={{ width: `${((setupStep + 1) / steps.length) * 100}%` }} /></div>
        <div className="vq-setup-card">
          <div className="vq-setup-kicker">A LITTLE ABOUT YOU</div>
          <h1 className="vq-setup-title">{step.title}</h1>
          <p className="vq-setup-sub">Pick as many as you want. Vestiq uses this profile when building your looks.</p>
          {setupStep === 0 && (
            <input className="vq-setup-input" placeholder="What should Vestiq call you?" value={setupData.name || displayName || ""} onChange={(e) => setSetupData((x) => ({ ...x, name: e.target.value }))} />
          )}
          <div className="vq-setup-options">
            {step.options.map((option) => {
              const value = step.single ? option.value : option;
              const label = step.single ? option.label : option;
              const selected = step.single ? setupData[step.field] === value : setupData[step.field]?.includes(value);
              return (
                <button key={value} type="button" aria-pressed={Boolean(selected)} className={`vq-setup-chip${selected ? " on" : ""}`} onClick={() => step.single ? setSetupData((current) => ({ ...current, [step.field]: value })) : toggleSetupValue(step.field, value)}>
                  {label}
                </button>
              );
            })}
          </div>
          <div className="vq-setup-actions">
            <button type="button" className="vq-setup-back" disabled={setupStep === 0} onClick={() => setSetupStep((x) => x - 1)}>← Back</button>
            {isLast ? <button type="button" className="vq-setup-next" onClick={completeSetup}>Finish my profile →</button> : <button type="button" className="vq-setup-next" onClick={() => setSetupStep((x) => x + 1)}>Continue →</button>}
          </div>
          {message && <div className="vq-setup-msg">{message}</div>}
        </div>
      </div>
    </div>
  );
}

function AppNav({ view, setView, displayName, dailyMood, onMood, onLogout }) {
  const [menuOpen, setMenuOpen] = useState(false);
  const go = (key) => { setView(key); setMenuOpen(false); };
  return (
    <nav className="navbar navbar-expand-lg bg-white border-bottom sticky-top vq-nav">
      <div className="container">
        <button className="navbar-brand vq-brand" onClick={() => go("home")} aria-label="Vestiq home"><img className="vq-brand-icon" src={vestiqLogoIcon} alt="" aria-hidden="true" /><span className="vq-wordmark">vesti<span>Q</span><i>✿</i></span></button>
        <button className="vq-burger" type="button" aria-label="Toggle menu" aria-expanded={menuOpen} onClick={() => setMenuOpen((o) => !o)}><span /><span /><span /></button>
        <div className={`vq-menu d-flex flex-wrap align-items-center gap-2 ${menuOpen ? "open" : ""}`}>
          {[['home','Home'],['wardrobe','My Wardrobe'],['style','Style Me'],['outfits','Outfits'],['profile','Profile']].map(([key,label]) => (
            <button key={key} className={`btn btn-sm ${view === key ? "btn-dark" : "btn-outline-secondary"}`} onClick={() => go(key)}>{label}</button>
          ))}
          <button className="btn btn-sm btn-outline-dark" onClick={() => { setMenuOpen(false); onMood(); }}>{dailyMood ? `Vibe: ${dailyMood}` : "Today's mood"}</button>
          <span className="small text-muted vq-username">{displayName}</span>
          <button className="btn btn-sm btn-link text-danger" onClick={onLogout}>Log out</button>
        </div>
      </div>
    </nav>
  );
}

function Dashboard({ name, todayLabel, greeting, dailyMood, wardrobe, recommendations, weather, weatherStatus, weatherError, onRetryWeather, onStyleMe, onWardrobe, onMood, onRefreshWardrobe }) {
  const firstName = (name || "there").split(" ")[0];
  return (
    <section className="vestiq-dashboard">
      <style>{`
        .vestiq-dashboard{--ink:#2b1930;--muted:#806b82;--line:#eadcea;--soft:#fbf7fc;color:var(--ink);padding:10px 0 42px}
        .vd-hero{position:relative;overflow:hidden;border:1px solid rgba(226,205,229,.85);border-radius:28px;padding:34px 36px;background:radial-gradient(circle at 92% 12%,rgba(214,157,235,.34),transparent 30%),linear-gradient(135deg,#fffaff,#f8f0fa 58%,#f5ecfb);box-shadow:0 18px 50px rgba(73,38,77,.08)}
        .vd-hero:after{content:"";position:absolute;width:190px;height:190px;border-radius:50%;right:-70px;bottom:-100px;background:rgba(210,166,237,.22);filter:blur(2px)}
        .vd-kicker{text-transform:uppercase;letter-spacing:2.4px;font-size:11px;font-weight:800;color:#9a739c;margin-bottom:9px}
        .vd-title{font-family:Georgia,"Times New Roman",serif;font-size:clamp(34px,4vw,54px);line-height:1.03;margin:0 0 10px;font-weight:500;letter-spacing:-1.2px}
        .vd-title em{color:#bb79bf;font-style:italic}
        .vd-sub{color:var(--muted);max-width:560px;margin:0;line-height:1.6}
        .vd-style-btn{border:0;border-radius:14px;padding:13px 19px;background:#321d38;color:white;font-weight:800;box-shadow:0 10px 24px rgba(50,29,56,.18);transition:.2s;position:relative;z-index:1}.vd-style-btn:hover{transform:translateY(-2px);box-shadow:0 14px 30px rgba(50,29,56,.24)}
        .vd-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:16px;margin-top:18px}.vd-card{background:rgba(255,255,255,.9);border:1px solid var(--line);border-radius:20px;padding:21px;box-shadow:0 10px 28px rgba(73,38,77,.055);transition:.2s}.vd-card:hover{transform:translateY(-2px);box-shadow:0 15px 34px rgba(73,38,77,.09)}
        .vd-label{font-size:12px;color:#967f98;font-weight:700;letter-spacing:.4px}.vd-value{font-size:25px;font-weight:850;margin:7px 0 12px}.vd-action{border:1px solid #dbc9df;background:#fff;border-radius:11px;padding:8px 12px;color:#4b3450;font-weight:700;font-size:13px;cursor:pointer}.vd-action:hover{background:#fbf3fd}
        .vd-flow{margin-top:18px;border-radius:22px;padding:23px 25px;background:#2f1c35;color:#fff;box-shadow:0 18px 40px rgba(47,28,53,.14)}.vd-flow-title{font-weight:800;font-size:18px}.vd-flow-copy{color:#d9c9db;font-size:13px;margin:4px 0 0}.vd-flow-steps{display:flex;flex-wrap:wrap;gap:8px;margin-top:16px}.vd-step{padding:8px 11px;border:1px solid rgba(255,255,255,.16);background:rgba(255,255,255,.07);border-radius:999px;font-size:12px;color:#f4eaf5}
        .vd-look{margin-top:18px}.vd-section-title{font-size:22px;font-weight:850;margin-bottom:12px}
        @media(max-width:850px){.vd-grid{grid-template-columns:1fr}.vd-hero{padding:26px 23px}.vd-style-btn{margin-top:15px}}
      `}</style>
      <div className="vd-hero d-flex flex-wrap justify-content-between align-items-end gap-4">
        <div>
          <div className="vd-kicker">{todayLabel}</div>
          <h1 className="vd-title">Hey, {firstName}! <em>What’s the vibe today?</em></h1>
          <p className="vd-sub">Your wardrobe is ready. Pick how you’re feeling and let Vestiq build from what you actually own.</p>
        </div>
        <button className="vd-style-btn" onClick={onStyleMe}>Style Me <span aria-hidden="true">→</span></button>
      </div>

      <div className="vd-grid">
        <div className="vd-card"><div className="vd-label">TODAY'S VIBE</div><div className="vd-value">{dailyMood || "Not set yet"}</div><button className="vd-action" onClick={onMood}>{dailyMood ? "Change mood" : "Choose mood"}</button></div>
        <div className="vd-card"><div className="vd-label">YOUR WARDROBE</div><div className="vd-value">{wardrobe.length} pieces</div><button className="vd-action" onClick={onWardrobe}>Open wardrobe</button></div>
        <div className="vd-card"><div className="vd-label">WEATHER</div>
          {weather ? (<><div className="vd-value">{`${weather.temperature}°`}</div><div className="vd-label">{weather.weather_condition}</div></>)
          : weatherStatus === "loading" ? (<><div className="vd-value">Checking…</div><div className="vd-label">Fetching today’s weather</div></>)
          : weatherStatus === "error" ? (<><div className="vd-value">Unavailable</div><div className="vd-label vq-weather-err">{weatherError}</div><button className="vd-action" onClick={onRetryWeather}>Retry</button></>)
          : (<><div className="vd-value">Not checked</div><div className="vd-label">Generate a look to check it</div></>)}
        </div>
      </div>

      <div className="vd-flow d-flex flex-wrap justify-content-between align-items-center gap-3">
        <div><div className="vd-flow-title">Your daily flow</div><p className="vd-flow-copy">Mood → weather → occasion → wardrobe → outfit.</p></div>
        <div className="vd-flow-steps"><span className="vd-step">✦ Personal style</span><span className="vd-step">☁ Weather-aware</span><span className="vd-step">♡ Your wardrobe</span></div>
      </div>

      {recommendations.length > 0 && <div className="vd-look"><div className="vd-section-title">Your latest looks</div>
<RecommendationCards
  recommendations={
    showAllRecommendations
      ? recommendations
      : recommendations.slice(0, 3)
  }
/>
{recommendations.length > 0 && (
  <div className="text-center mt-4">
    <button
      className="btn btn-outline-dark"
      onClick={() => setShowAllRecommendations((prev) => !prev)}
    >
      {showAllRecommendations ? "Show Less" : "Show More"}
    </button>
  </div>
)}
</div>}
      {wardrobe.length === 0 && <div className="vd-card mt-3"><div className="vd-label">NEXT STEP</div><div className="vd-value" style={{fontSize:22}}>Your wardrobe is waiting.</div><p className="vd-sub mb-3">Add your first clothing piece from a photo, gallery, or camera. Vestiq will use it for your future looks.</p><button className="vd-action" onClick={onWardrobe}>Add your first piece →</button></div>}
    </section>
  );
}

function WardrobeView(props) {
  return (
    <>
      <div className="d-flex justify-content-between align-items-end mb-3"><div><h1 className="fw-bold mb-1">My Wardrobe</h1><p className="text-muted mb-0">Add clothes once. Vestiq can use them again and again.</p></div><button className="btn btn-outline-dark" onClick={props.onRefresh}>Refresh</button></div>

      <div className="card border-0 shadow-sm mb-4">
        <div className="card-body">
          <h4 className="fw-bold">Add clothing</h4>
          <p className="text-muted small mb-3">Upload a photo or use your camera. Choose the details yourself before saving.</p>
          <div className="row g-2 align-items-center">
            <div className="col-md-8"><input id="clothing-file" type="file" accept="image/*" className="form-control" onChange={(e) => props.setImage(e.target.files?.[0] || null)} /></div>
            <div className="col-md-2"><button className="btn btn-outline-dark w-100" onClick={props.openCamera} disabled={props.cameraLoading}>{props.cameraLoading ? "Opening..." : "Use Camera"}</button></div>
            <div className="col-md-2"><button className="btn btn-dark w-100" onClick={props.uploadClothing} disabled={props.busy || !props.image}>{props.busy ? "Saving..." : "Review & Add"}</button></div>
          </div>
          {props.cameraOpen && <div className="mt-3"><video ref={props.videoRef} autoPlay playsInline muted className="w-100 rounded" style={{ maxHeight: 360, background: "#111", objectFit: "cover" }} /><div className="mt-2"><button className="btn btn-dark me-2" onClick={props.capturePhoto}>Capture</button><button className="btn btn-outline-secondary" onClick={props.closeCamera}>Close</button></div></div>}
          {props.image && <div className="small text-muted mt-2">Ready: {props.image.name}</div>}
        </div>
      </div>

      <div className="d-flex gap-2 flex-wrap mb-3"><button className={`btn ${props.filter === "all" ? "btn-dark" : "btn-outline-dark"}`} onClick={() => props.setFilter("all")}>All</button>{props.categories.map((x) => <button key={x} className={`btn btn-sm ${props.filter === x ? "btn-dark" : "btn-outline-secondary"}`} onClick={() => props.setFilter(x)}>{x}</button>)}</div>
      <div className="row g-3">{props.wardrobe.length === 0 ? <div className="col-12"><div className="card border-0 shadow-sm"><div className="card-body text-muted">No clothing items in this view yet.</div></div></div> : props.wardrobe.map((item) => {
        const wornToday = Boolean(item.last_worn_at);
        return <div className="col-md-4" key={item.id}><div className="card border-0 shadow-sm h-100">{item.image_url && <img src={item.image_url} alt={item.name} className="card-img-top" style={{ height: 300, objectFit: "contain", background: "#f8f3f8", padding: "8px" }} />}{!item.image_url && <div className="bg-light" style={{ height: 180 }} />}<div className="card-body"><h5 className="fw-bold">{item.name}</h5><div className="small text-muted">{item.category || "Uncategorized"}{item.color ? ` • ${item.color}` : ""}</div>{item.domain && <div className="small mt-2">Domain: {domainLabel(item.domain)}</div>}{item.style && <div className="small mt-1">Style: {displayLabel(item.style)}</div>}{Array.isArray(item.occasion_tags) && item.occasion_tags.length > 0 && <div className="small mt-1">Occasions: {item.occasion_tags.map((x) => displayLabel(x)).join(" • ")}</div>}{item.last_worn_at && <div className="small text-muted mt-2">Last worn: {new Date(item.last_worn_at).toLocaleDateString()}</div>}<div className="d-flex flex-wrap gap-2 mt-3 vq-actions"><button className={`btn vq-act ${wornToday ? "btn-dark vq-act-undo" : "btn-outline-dark vq-act-worn"} flex-grow-1`} onClick={() => wornToday ? props.undoWorn(item.id) : props.markAsWorn(item.id)}>{wornToday ? "Undo Worn Today" : "Worn Today"}</button><button className="btn btn-outline-danger vq-act vq-act-del" onClick={() => props.deleteClothing(item.id, item.name)}>Delete</button></div></div></div></div>;
      })}</div>
    </>
  );
}

function StyleView({
  dailyMood,
  onMood,
  occasion,
  setOccasion,
  recommendationDate,
  setRecommendationDate,
  stylistPrompt,
  setStylistPrompt,
  onGenerate,
  loading,
  weather,
  recommendations,
  saveOutfit,
  wearOutfit,
  rateOutfit,
  ratings
}) {
    const [showAllRecommendations, setShowAllRecommendations] = useState(false);
  const [styleQuestionsOpen, setStyleQuestionsOpen] = useState(false);

  const [stylePreferences, setStylePreferences] = useState({
    top: "Anything",
    bottom: "Anything",
    vibe: "No preference",
    colour: "No preference",
    specific: ""
  });

  const updatePreference = (key, value) => {
    setStylePreferences((prev) => ({
      ...prev,
      [key]: value
    }));
  };

  const buildMyLooks = () => {
    const preferenceText = [
      `Top preference: ${stylePreferences.top}`,
      `Bottom preference: ${stylePreferences.bottom}`,
      `Vibe: ${stylePreferences.vibe}`,
      `Colour preference: ${stylePreferences.colour}`,
      stylePreferences.specific
        ? `Anything specific: ${stylePreferences.specific}`
        : ""
    ]
      .filter(Boolean)
      .join(". ");

    // Keep the existing "Anything else?" request and add
    // the new detailed preferences to it.
    const combinedPrompt = stylistPrompt.trim()
      ? `${stylistPrompt.trim()}. ${preferenceText}`
      : preferenceText;

    setStylistPrompt(combinedPrompt);

    setStyleQuestionsOpen(false);
    onGenerate(occasion, combinedPrompt);
  };

  return (
    <>
      <div className="d-flex flex-wrap justify-content-between align-items-end gap-3 mb-4">
        <div>
          <div className="vq-kicker">FIT CHECK</div>
          <h1 className="fw-bold mb-1">Style Me</h1>
          <p className="text-muted mb-0">
            Pick the moment, add a vibe, and Vestiq builds your fit from clothes you actually own.
          </p>
        </div>

        <button className="btn btn-outline-dark" onClick={onMood}>
          {dailyMood ? `Today's mood: ${dailyMood}` : "Choose today's mood"}
        </button>
      </div>

      <div className="card border-0 shadow-sm mb-4 vq-style-form">
        <div className="card-body">
          <div className="row g-3 align-items-end">

            <div className="col-md-4">
              <label className="form-label">Occasion</label>
              <select
                className="form-select"
                value={occasion}
                onChange={(e) => setOccasion(e.target.value)}
              >
                {OCCASIONS.map((x) => (
                  <option key={x}>{x}</option>
                ))}
              </select>
            </div>

            <div className="col-md-4">
              <label className="form-label">Date</label>
              <input
                type="date"
                className="form-control"
                value={recommendationDate}
                onChange={(e) => setRecommendationDate(e.target.value)}
              />
            </div>

            <div className="col-md-4">
              <label className="form-label">Anything else?</label>
              <input
                className="form-control"
                placeholder="e.g. elegant black look"
                value={stylistPrompt}
                onChange={(e) => setStylistPrompt(e.target.value)}
              />
            </div>

            <div className="col-12">
              <button
                className="btn btn-dark"
                onClick={() => setStyleQuestionsOpen(true)}
                disabled={loading}
              >
                {loading ? "Styling your wardrobe..." : "Let’s build your fit →"}
              </button>
            </div>

          </div>
        </div>
      </div>

      {weather && (
        <div className="alert alert-light border">
          Weather: <strong>{weather.temperature}°</strong> ·{" "}
          {weather.weather_condition}
          {weather.rain_probability != null
            ? ` · Rain ${weather.rain_probability}%`
            : ""}
        </div>
      )}

{import.meta.env.DEV && <p className="vq-dev-note">dev · {recommendations.length} recommendations received</p>}

     
{recommendations.length > 0 ? (
  <>
    <RecommendationCards
      recommendations={
        showAllRecommendations
          ? recommendations
          : recommendations.slice(0, 3)
      }
      saveOutfit={saveOutfit}
      wearOutfit={wearOutfit}
      rateOutfit={rateOutfit}
      ratings={ratings}
      interactive
    />

    {recommendations.length > 3 && (
      <div className="text-center mt-4">
        <button
          type="button"
          className="btn btn-outline-dark"
          onClick={() =>
            setShowAllRecommendations((current) => !current)
          }
        >
          {showAllRecommendations ? "Show Less" : "Show More"}
        </button>
      </div>
    )}
  </>
) : loading ? (
  <div className="card border-0 shadow-sm vq-state vq-loading" role="status" aria-live="polite">
    <div className="card-body p-5 text-center"><span className="vq-spinner" aria-hidden="true" /><div className="vq-state-title">Fit check in progress…</div><div className="text-muted">Mixing your wardrobe with today’s mood, weather and occasion.</div></div>
  </div>
) : (
  <div className="card border-0 shadow-sm vq-state">
    <div className="card-body p-5 text-center"><div className="vq-state-title">Your fits will show up here ✦</div><div className="text-muted">Choose an occasion, add anything specific, then hit “Let’s build your fit”.</div></div>
  </div>
)}

      {styleQuestionsOpen && (
        <div
          style={{
            position: "fixed",
            inset: 0,
            background: "rgba(0,0,0,0.45)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            zIndex: 2000,
            padding: "20px"
          }}
        >
          <div
  className="card border-0 shadow-lg"
  style={{
    width: "100%",
    maxWidth: "760px",
    maxHeight: "85vh",
    overflowY: "auto",
    borderRadius: "22px",
    background: "#fffaff"
  }}
>
            <div className="card-body p-4">

              <div className="d-flex justify-content-between align-items-start mb-4">
                <div>
                  <h3 className="fw-bold mb-1">Tell me what you're in the mood for</h3>
                  <p className="text-muted mb-0">
                    A few preferences will help Vestiq create a more precise look.
                  </p>
                </div>

                <button
                  type="button"
                  className="btn-close"
                  onClick={() => setStyleQuestionsOpen(false)}
                />
              </div>

              {/* TOP */}
              <div className="mb-4">
                <label className="form-label fw-semibold">
                  What type of top are you feeling like wearing?
                </label>

                <div className="d-flex flex-wrap gap-2">
  {[
    "Anything",
    "T-shirt",
    "Casual top",
    "Shirt",
    "Kurti",
    "Dress",
    "Traditional",
    "Indo-Western"
  ].map((option) => (
    <button
      key={option}
      type="button"
      onClick={() => updatePreference("top", option)}
      style={{
        borderRadius: "18px",
        padding: "8px 15px",
        border: `1px solid ${
          stylePreferences.top === option ? "#c58bea" : "#ead8ed"
        }`,
        background:
          stylePreferences.top === option ? "#f1ddfa" : "#fff",
        color: "#4d3b55",
        fontWeight: stylePreferences.top === option ? 700 : 500,
        cursor: "pointer"
      }}
    >
      {option}
    </button>
  ))}
</div>
              </div>
              

              {/* BOTTOM */}
              <div className="mb-4">
                <label className="form-label fw-semibold">
                  What type of bottom would you prefer?
                </label>

                <div className="d-flex flex-wrap gap-2">
  {[
    "No bottom / One-piece",
    "Jeans",
    "Straight-fit jeans",
    "Wide-leg jeans",
    "Bell-bottom / Flared",
    "Trousers",
    "Palazzo",
    "Skirt",
    "Anything"
  ].map((option) => (
    <button
      key={option}
      type="button"
      onClick={() => updatePreference("bottom", option)}
      style={{
        borderRadius: "18px",
        padding: "8px 15px",
        border: `1px solid ${
          stylePreferences.bottom === option ? "#c58bea" : "#ead8ed"
        }`,
        background:
          stylePreferences.bottom === option ? "#f1ddfa" : "#fff",
        color: "#4d3b55",
        fontWeight: stylePreferences.bottom === option ? 700 : 500,
        cursor: "pointer"
      }}
    >
      {option}
    </button>
  ))}
</div>
              </div>
{/* VIBE */}
<div className="mb-4">
  <label className="form-label fw-semibold">
    What kind of vibe do you want?
  </label>

  <div className="d-flex flex-wrap gap-2">
    {[
      "No preference",
      "Simple & comfortable",
      "Cute",
      "Trendy",
      "Elegant",
      "Chill",
      "Dressy"
    ].map((option) => (
      <button
        key={option}
        type="button"
        onClick={() => updatePreference("vibe", option)}
        style={{
          borderRadius: "18px",
          padding: "8px 15px",
          border: `1px solid ${
            stylePreferences.vibe === option ? "#c58bea" : "#ead8ed"
          }`,
          background:
            stylePreferences.vibe === option ? "#f1ddfa" : "#fff",
          color: "#4d3b55",
          fontWeight: stylePreferences.vibe === option ? 700 : 500,
          cursor: "pointer"
        }}
      >
        {option}
      </button>
    ))}
  </div>
</div>

              <div className="mb-4">
                <label className="form-label fw-semibold">
                  Any colour preference?
                </label>

                <div className="d-flex flex-wrap gap-2">
  {[
    "Black",
    "White",
    "Blue",
    "Pink",
    "Pastel",
    "Beige",
    "No preference"
  ].map((option) => (
    <button
      key={option}
      type="button"
      onClick={() => updatePreference("colour", option)}
      style={{
        borderRadius: "18px",
        padding: "8px 15px",
        border: `1px solid ${
          stylePreferences.colour === option ? "#c58bea" : "#ead8ed"
        }`,
        background:
          stylePreferences.colour === option ? "#f1ddfa" : "#fff",
        color: "#4d3b55",
        fontWeight: stylePreferences.colour === option ? 700 : 500,
        cursor: "pointer"
      }}
    >
      {option}
    </button>
  ))}
</div>
              </div>

              {/* SPECIFIC REQUEST */}
              <div className="mb-4">
                <label className="form-label fw-semibold">
                  Anything specific you want?
                </label>

                <input
                  className="form-control"
                  placeholder="e.g. pink top with blue wide-leg jeans"
                  value={stylePreferences.specific}
                  onChange={(e) =>
                    updatePreference("specific", e.target.value)
                  }
                />
              </div>

              <div className="d-flex justify-content-end gap-2">
                <button
                  type="button"
                  className="btn btn-outline-secondary"
                  onClick={() => setStyleQuestionsOpen(false)}
                >
                  Cancel
                </button>

                <button
                  type="button"
                  className="btn btn-dark"
                  onClick={buildMyLooks}
                  disabled={loading}
                >
                  {loading ? "Styling your wardrobe..." : "Build my looks →"}
                </button>
              </div>

            </div>
          </div>
        </div>
      )}
    </>
  );
}

function RecommendationCards({ recommendations, saveOutfit, onRemove, wearOutfit, rateOutfit, ratings, interactive = false }) {
  return <div className="row g-3">{recommendations.map((outfit, index) => <div className="col-lg-4" key={`${outfitKeyLocal(outfit)}-${index}`}><div className="card border-0 shadow-sm h-100"><div className="row g-0">{[outfit.top, outfit.bottom].map((item) => item ? <div className="col-6" key={item.id}>{item.image_url ? <img src={item.image_url} alt={item.name} className="w-100" style={{ height: 220, objectFit: "contain", background: "#f8f3f8", padding: "6px" }} /> : <div className="bg-light" style={{ height: 180 }} />}<div className="small p-2">{item.name}</div></div> : null)}</div><div className="card-body"><h5 className="fw-bold">Look {index + 1}</h5>{outfit.reasons?.map((reason, i) => <div className="small text-muted" key={i}>• {reason}</div>)}<div className="d-flex gap-2 mt-3 flex-wrap"><span className="badge bg-dark">Score {outfit.score}</span>{interactive && <>{onRemove ? <button className="btn btn-sm vq-remove-btn" onClick={() => onRemove(outfit)}>Remove</button> : <button className="btn btn-sm btn-outline-dark" onClick={() => saveOutfit(outfit)}>Save</button>}<button className="btn btn-sm btn-outline-dark" onClick={() => wearOutfit(outfit)}>Wear</button></>}</div>{interactive && <div className="mt-3">Rate: {[1,2,3,4,5].map((rating) => <button key={rating} className={`btn btn-sm ${ratings[outfitKeyLocal(outfit)] === rating ? "btn-dark" : "btn-outline-secondary"} me-1`} onClick={() => rateOutfit(outfit, rating)}>{rating}</button>)}</div>}</div></div></div>)}</div>;
}

function outfitKeyLocal(outfit) { return `${outfit?.top?.id || "none"}-${outfit?.bottom?.id || "none"}`; }

function OutfitsView({ recommendations, savedOutfits, removeSavedOutfit, history, saveOutfit, wearOutfit, rateOutfit, ratings }) {
  return <>
    <h1 className="fw-bold">Outfits</h1><p className="text-muted">Your saved looks and what you have worn.</p>
    <h4 className="fw-bold mt-4 mb-3">Saved looks</h4>
    {savedOutfits.length ? <RecommendationCards recommendations={savedOutfits.map((x) => x.outfit)} saveOutfit={saveOutfit} onRemove={removeSavedOutfit} wearOutfit={wearOutfit} rateOutfit={rateOutfit} ratings={ratings} interactive /> : <div className="card border-0 shadow-sm"><div className="card-body text-muted">Save an outfit from Style Me and it will appear here.</div></div>}
    <h4 className="fw-bold mt-5 mb-3">Wear history</h4>
    {history.length ? <div className="vq-history-list">{history.slice(0, 10).map((entry) => {
      const pieces = [entry.outfit?.top, entry.outfit?.bottom].filter(Boolean);
      return <div className="vq-history-row" key={entry.key}>
        <div className="vq-history-thumbs">
          {pieces.map((item, i) => <figure key={`${item.id || "item"}-${i}`}>
            {item.image_url ? <img src={item.image_url} alt={item.name || "Outfit piece"} /> : <div className="vq-history-ph" />}
            <figcaption>{item.name || "Piece"}</figcaption>
          </figure>)}
        </div>
        <div className="vq-history-meta">
          <span className="vq-history-label">Worn on</span>
          <strong>{new Date(entry.wornAt).toLocaleDateString(undefined, { day: "numeric", month: "short", year: "numeric" })}</strong>
          <span className="vq-history-names">{pieces.map((item) => item.name).join(" + ")}</span>
        </div>
      </div>;
    })}</div> : <div className="card border-0 shadow-sm"><div className="card-body text-muted">No outfit history yet.</div></div>}
    {recommendations.length > 0 && <><h4 className="fw-bold mt-5 mb-3">Latest recommendations</h4><RecommendationCards recommendations={recommendations} saveOutfit={saveOutfit} wearOutfit={wearOutfit} rateOutfit={rateOutfit} ratings={ratings} interactive /></>}
  </>;
}

function ProfileView({ displayName, setupData, setSetupData, onReopenSetup, dailyMood, onMood, history, saved }) {
  return <>
    <div className="d-flex justify-content-between align-items-end mb-4"><div><h1 className="fw-bold">Profile</h1><p className="text-muted mb-0">Your style profile shapes future recommendations.</p></div><button className="btn btn-outline-dark" onClick={onReopenSetup}>Edit style profile</button></div>
    <div className="row g-3"><div className="col-md-6"><div className="card border-0 shadow-sm h-100"><div className="card-body"><h5 className="fw-bold">About you</h5><p className="mb-1">Name: {displayName}</p><p className="mb-0">Today's mood: {dailyMood || "Not set"}</p><button className="btn btn-sm btn-outline-dark mt-3" onClick={onMood}>Change mood</button></div></div></div><div className="col-md-6"><div className="card border-0 shadow-sm h-100"><div className="card-body"><h5 className="fw-bold">Style preferences</h5><p className="small mb-1">Vibe: {(setupData.vibes || []).join(", ") || "Not set"}</p><p className="small mb-1">Occasions: {(setupData.occasions || []).join(", ") || "Not set"}</p><p className="small mb-1">Palette: {(setupData.palette || []).join(", ") || "Not set"}</p><p className="small mb-0">Clothing: {(setupData.clothing || []).join(", ") || "Not set"}</p></div></div></div><div className="col-12"><div className="card border-0 shadow-sm"><div className="card-body"><h5 className="fw-bold">Vestiq memory</h5><div className="d-flex gap-4"><span>{saved.length} saved looks</span><span>{history.length} worn looks</span></div></div></div></div></div>
  </>;
}

function ClothingReviewModal({ review, onChange, onConfirm, onCancel, busy, nameOptions, categoryOptions, error }) {
  if (!review) return null;
  const selectedOccasions = normalizeOccasionTags(review.occasion_tags);
  const toggleOccasion = (value) => {
    const current = normalizeOccasionTags(review.occasion_tags);
    const next = current.includes(value) ? current.filter((x) => x !== value) : [...current, value];
    onChange("occasion_tags", next);
  };
  const fieldOptions = (options, includeOther = true) => {
    const unique = [...new Set(options.map((x) => String(x)))];
    return includeOther && !unique.includes("Other") ? [...unique, "Other"] : unique;
  };
  const selectValue = (value) => value === "__other__" ? "Other" : value || "";
  return (
    <div className="vestiq-review-overlay" role="dialog" aria-modal="true" aria-label="Choose clothing details">
      <style>{`
        .vestiq-review-overlay{position:fixed;inset:0;z-index:3100;display:flex;align-items:center;justify-content:center;padding:22px;background:rgba(35,18,39,.45);backdrop-filter:blur(13px)}
        .vestiq-review-card{width:min(820px,95vw);max-height:92vh;overflow:auto;border:1px solid rgba(255,255,255,.76);border-radius:28px;background:linear-gradient(145deg,rgba(255,252,255,.99),rgba(249,241,252,.98));box-shadow:0 30px 100px rgba(38,18,43,.30);padding:28px;animation:vdReviewIn .24s ease-out}
        @keyframes vdReviewIn{from{opacity:0;transform:translateY(12px) scale(.985)}to{opacity:1;transform:none}}
        .vd-review-grid{display:grid;grid-template-columns:230px 1fr;gap:24px;align-items:start}.vd-review-image{width:100%;height:330px;border-radius:20px;object-fit:contain;background:#f8f3f8;border:1px solid #eadceb;padding:8px;box-sizing:border-box}.vd-review-kicker{text-transform:uppercase;letter-spacing:2px;font-size:10px;font-weight:850;color:#aa7cab;margin-bottom:7px}.vd-review-title{font-family:Georgia,"Times New Roman",serif;font-size:30px;line-height:1.08;color:#321d38;margin:0}.vd-review-copy{color:#806b82;font-size:13px;margin:8px 0 18px}.vd-review-warning{padding:10px 12px;border-radius:13px;background:#fff6dc;border:1px solid #f1dfaa;color:#765f20;font-size:12px;margin-bottom:16px}.vd-review-field label{font-size:11px;font-weight:800;color:#725878;text-transform:uppercase;letter-spacing:.7px;margin-bottom:5px}.vd-review-custom{margin-top:6px}.vd-review-occasions{display:flex;flex-wrap:wrap;gap:8px;margin-top:6px}.vd-review-occasion{border:1px solid #e3d4e5;background:#fff;border-radius:999px;padding:8px 11px;color:#674d6b;font-size:12px;font-weight:700;cursor:pointer;transition:.16s}.vd-review-occasion.selected{background:#321d38;color:#fff;border-color:#321d38;box-shadow:0 5px 12px rgba(50,29,56,.16)}.vd-review-hint{font-size:11px;color:#907d91;margin-top:7px}.vd-review-footer{display:flex;justify-content:flex-end;gap:10px;margin-top:22px;padding-top:18px;border-top:1px solid #eee2ef}@media(max-width:700px){.vd-review-grid{grid-template-columns:1fr}.vd-review-image{height:260px}.vestiq-review-card{padding:22px}}
      `}</style>
      <div className="vestiq-review-card">
        <div className="vd-review-grid">
          <div>{review.image_url ? <img src={review.image_url} alt="Clothing preview" className="vd-review-image" /> : <div className="vd-review-image" />}</div>
          <div>
            <div className="vd-review-kicker">WARDROBE DETAILS</div>
            <h2 className="vd-review-title">Looks good? You decide.</h2>
            <p className="vd-review-copy">Choose the details that best describe this clothing piece before adding it to your wardrobe.</p>
            
            <div className="row g-2">
              <div className="col-md-6 vd-review-field"><label>Name</label><select className="form-select" value={selectValue(review.name)} onChange={(e) => onChange("name", e.target.value === "Other" ? "__other__" : e.target.value)}><option value="">Choose a clothing name</option>{fieldOptions(nameOptions).map((x) => <option key={x} value={x}>{x}</option>)}</select>{review.name === "__other__" && <input className="form-control vd-review-custom" placeholder="Type clothing name" value={review.custom_name || ""} onChange={(e) => onChange("custom_name", e.target.value)} />}</div>
              <div className="col-md-6 vd-review-field"><label>Domain</label><select className="form-select" value={review.domain || ""} onChange={(e) => onChange("domain", e.target.value)}><option value="">Choose a domain</option>{DOMAIN_OPTIONS.map((x) => <option key={x} value={x}>{domainLabel(x)}</option>) }</select></div>
              <div className="col-md-6 vd-review-field"><label>Category</label><select className="form-select" value={selectValue(review.category)} onChange={(e) => onChange("category", e.target.value === "Other" ? "__other__" : e.target.value)}><option value="">Choose a category</option>{fieldOptions(categoryOptions).map((x) => <option key={x} value={x}>{displayLabel(x)}</option>)}</select>{review.category === "__other__" && <input className="form-control vd-review-custom" placeholder="e.g. jumpsuit, gown, co-ord set" value={review.custom_category || ""} onChange={(e) => onChange("custom_category", e.target.value)} />}</div>
              <div className="col-md-6 vd-review-field"><label>Colour</label><select className="form-select" value={selectValue(review.color)} onChange={(e) => onChange("color", e.target.value === "Other" ? "__other__" : e.target.value)}><option value="">Choose a colour</option>{fieldOptions(REVIEW_COLOR_OPTIONS).map((x) => <option key={x} value={x}>{x}</option>)}</select>{review.color === "__other__" && <input className="form-control vd-review-custom" placeholder="Type colour" value={review.custom_color || ""} onChange={(e) => onChange("custom_color", e.target.value)} />}</div>
              <div className="col-md-6 vd-review-field"><label>Style</label><select className="form-select" value={selectValue(review.style)} onChange={(e) => onChange("style", e.target.value === "Other" ? "__other__" : e.target.value)}><option value="">Choose a style</option>{fieldOptions(REVIEW_STYLE_OPTIONS).map((x) => <option key={x} value={x}>{x}</option>)}</select>{review.style === "__other__" && <input className="form-control vd-review-custom" placeholder="e.g. preppy, glam, vacation" value={review.custom_style || ""} onChange={(e) => onChange("custom_style", e.target.value)} />}</div>
              <div className="col-md-6 vd-review-field"><label>Weight</label><select className="form-select" value={review.outfit_weight || ""} onChange={(e) => onChange("outfit_weight", e.target.value)}><option value="">Choose a weight</option><option value="light">Light</option><option value="medium">Medium</option><option value="heavy">Heavy</option></select></div>
              <div className="col-12 vd-review-field"><label>Where can you wear this? Select all that apply</label><div className="vd-review-occasions">{REVIEW_OCCASION_OPTIONS.map((x) => { const value = x.toLowerCase(); const selected = selectedOccasions.includes(value); return <button type="button" key={x} className={`vd-review-occasion ${selected ? "selected" : ""}`} onClick={() => toggleOccasion(value)}>{x}</button>; })}</div>{selectedOccasions.includes("other") && <input className="form-control vd-review-custom" placeholder="Type another occasion" value={review.custom_occasion || ""} onChange={(e) => onChange("custom_occasion", e.target.value)} />}<div className="vd-review-hint">For example, a saree can be selected for Wedding + Festive + Party at the same time.</div></div>
            </div>
          </div>
        </div>
        {error && <div className="vd-review-warning" role="alert">{error}</div>}
        <div className="vd-review-footer"><button className="btn btn-outline-secondary" onClick={onCancel} disabled={busy}>Cancel</button><button className="btn btn-dark" onClick={onConfirm} disabled={busy}>{busy ? "Saving..." : "Confirm & Add to Wardrobe"}</button></div>
      </div>
    </div>
  );
}

function StyleBuddyLauncher({ visible, apiUrl, token, userName }) {
  const [panel, setPanel] = useState("closed"); // closed | open | min
  const [everOpened, setEverOpened] = useState(false);
  const openChat = () => { setPanel("open"); setEverOpened(true); };
  // Centered chat: Esc closes it, and the page behind it does not scroll.
  useEffect(() => {
    if (panel !== "open") return undefined;
    const onKey = (event) => { if (event.key === "Escape") setPanel("closed"); };
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    window.addEventListener("keydown", onKey);
    return () => {
      window.removeEventListener("keydown", onKey);
      document.body.style.overflow = previousOverflow;
    };
  }, [panel]);
  return (
    <div className="vq-chat-root" style={{ display: visible ? "block" : "none" }}>
      {panel === "open" && <div className="vq-chat-backdrop" onClick={() => setPanel("closed")} aria-hidden="true" />}
      {everOpened && (
        <section className={`vq-chat-panel ${panel === "min" ? "is-min" : ""}`} role="dialog" aria-label={`${CHATBOT_NAME} — ${CHATBOT_SUBTITLE}`} hidden={panel === "closed"}>
          <header className="vq-chat-head">
            <div className="vq-chat-title"><span className="vq-chat-avatar" aria-hidden="true">M</span><div><strong>{CHATBOT_NAME}</strong><small>{CHATBOT_SUBTITLE}</small></div></div>
            <div className="vq-chat-controls">
              <button type="button" aria-label={panel === "min" ? "Expand chat" : "Minimize chat"} onClick={() => setPanel(panel === "min" ? "open" : "min")}>{panel === "min" ? "▢" : "–"}</button>
              <button type="button" aria-label="Close chat" onClick={() => setPanel("closed")}>×</button>
            </div>
          </header>
          <div className="vq-chat-body" hidden={panel === "min"}>
            <StylistChat apiUrl={apiUrl} token={token} userName={userName} onOpenStyleMe={() => setPanel("min")} />
          </div>
        </section>
      )}
      {panel === "closed" && (
        <div className="vq-orb-wrap">
          <div className="vq-orb-hint" role="tooltip" id="vq-orb-hint">Chat with MIRA, your personal AI stylist</div>
          <span className="vq-orb-bubble b1" aria-hidden="true" /><span className="vq-orb-bubble b2" aria-hidden="true" /><span className="vq-orb-bubble b3" aria-hidden="true" />
          <button type="button" className="vq-chat-fab" onClick={openChat} aria-label={`Open ${CHATBOT_NAME} — ${CHATBOT_SUBTITLE}`} aria-describedby="vq-orb-hint">
            <svg viewBox="0 0 24 24" width="30" height="30" aria-hidden="true"><path fill="#fff" d="M12 3C6.9 3 3 6.6 3 11.1c0 2.3 1.1 4.4 2.9 5.8L5 21l4.1-1.9c.9.2 1.9.3 2.9.3 5.1 0 9-3.6 9-8.1S17.1 3 12 3Z"/><path fill="#b56fc4" d="m12 6.5.9 2.3 2.3.9-2.3.9-.9 2.3-.9-2.3-2.3-.9 2.3-.9Z"/></svg>
          </button>
        </div>
      )}
    </div>
  );
}

function MoodModal({ current, onSelect, onClose }) {
  const moodMeta = {
    "Chill": ["😌", "easy, comfy, no pressure"],
    "Cute": ["🎀", "soft, pretty, playful"],
    "Confident": ["✨", "walk in like you own it"],
    "Main Character": ["💅", "today is about you"],
    "Soft": ["🌷", "calm, feminine, effortless"],
    "Low-key / Don't talk to me": ["🫠", "comfy and keeping it low-key"],
    "Dress to impress": ["🥂", "we are making an entrance"],
    "Keep it simple": ["🤍", "clean, easy, done"],
  };
  const moodCardRef = useRef(null);
  useEffect(() => {
    const onKey = (event) => { if (event.key === "Escape") onClose(); };
    document.addEventListener("keydown", onKey);
    const target = moodCardRef.current?.querySelector(".vd-mood-option.selected") || moodCardRef.current?.querySelector(".vd-mood-option");
    target?.focus({ preventScroll: true });
    return () => document.removeEventListener("keydown", onKey);
  }, []);
  return (
    <div className="vestiq-mood-overlay" role="dialog" aria-modal="true" aria-labelledby="vq-mood-title" onMouseDown={(event) => { if (event.target === event.currentTarget) onClose(); }}>
      <div className="vestiq-mood-card" ref={moodCardRef}>
        <button type="button" className="vd-mood-close" onClick={onClose} aria-label="Close">×</button>
        <div className="vd-moods">
          <div className="vq-cloud-main">
            <svg className="vq-cloud-svg" viewBox="0 0 440 280" preserveAspectRatio="none" aria-hidden="true">
              <defs>
                <linearGradient id="vqCloudFill" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stopColor="#ffd9f0" stopOpacity=".95" /><stop offset=".55" stopColor="#e6d6ff" stopOpacity=".92" /><stop offset="1" stopColor="#cfe0ff" stopOpacity=".9" /></linearGradient>
              </defs>
              <path d="M112 246C52 246 18 205 36 163C14 120 56 76 106 90C124 42 196 24 236 60C262 34 326 44 340 92C396 90 424 148 388 182C414 222 372 250 322 244C290 262 240 262 214 246C186 262 140 262 112 246Z" fill="url(#vqCloudFill)" />
            </svg>
            <div className="vq-cloud-copy">
              <div className="vd-mood-eyebrow">Daily vibe check</div>
              <h2 className="vd-mood-title" id="vq-mood-title">What’s your vibe today?</h2>
              <p className="vd-mood-copy">No overthinking. Pick what feels like you right now.</p>
            </div>
          </div>
          {MOODS.map((mood) => { const [emoji, desc] = moodMeta[mood] || ["✦", "your vibe, your rules"]; return <button type="button" key={mood} aria-pressed={current === mood} className={`vd-mood-option ${current === mood ? "selected" : ""}`} onClick={() => onSelect(mood)}><span className="vd-mood-emoji">{emoji}</span><span className="vd-mood-text"><span className="vd-mood-name">{mood}</span><span className="vd-mood-desc">{desc}</span></span></button>; })}
        </div>
        <div className="vd-mood-footer"><span>Vestiq uses this to personalize today’s look.</span><button type="button" className="vd-mood-skip" onClick={onClose}>Not now</button></div>
      </div>
    </div>
  );
}

export default App;