// Purpose: landing page with navbar, hero and mobile menu
import React, { useEffect, useState } from "react";
import "./landing.css";
import landingBg from "../assets/vestiq-landing-bg.png";
import vestiqLogoIcon from "../assets/vestiq-logo.png";

const GITHUB_URL = "https://github.com/"; // Replace only with your Vestiq repository URL.

const sections = ["home", "features", "how", "about"];

export default function LandingPage({ onEnter }) {
  const [activeSection, setActiveSection] = useState("home");
  const [menuOpen, setMenuOpen] = useState(false);

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        const visible = entries
          .filter((entry) => entry.isIntersecting)
          .sort((a, b) => b.intersectionRatio - a.intersectionRatio)[0];
        if (visible) setActiveSection(visible.target.id);
      },
      { rootMargin: "-18% 0px -55% 0px", threshold: [0.15, 0.35, 0.6] }
    );

    sections.forEach((id) => {
      const element = document.getElementById(id);
      if (element) observer.observe(element);
    });

    return () => observer.disconnect();
  }, []);

  const scrollTo = (id) => {
    setMenuOpen(false);
    document.getElementById(id)?.scrollIntoView({ behavior: "smooth", block: "start" });
  };

  return (
    <main className="vestiq-landing-page">
      <img className="vestiq-landing-bg" src={landingBg} alt="" aria-hidden="true" />
      <div className="vestiq-overlay" />
      <div className="vestiq-frame" aria-hidden="true" />

      <header className="vestiq-nav">
        <button className="vestiq-logo" onClick={() => scrollTo("home")} aria-label="Vestiq home">
          <img className="vestiq-logo-icon" src={vestiqLogoIcon} alt="" aria-hidden="true" />
          <span className="vestiq-wordmark">vesti<span>Q</span><i>✿</i></span>
        </button>

        <button
          className="vestiq-menu-toggle"
          type="button"
          aria-label={menuOpen ? "Close menu" : "Open menu"}
          aria-expanded={menuOpen}
          aria-controls="vestiq-mobile-menu"
          onClick={() => setMenuOpen((open) => !open)}
        >
          <span />
          <span />
          <span />
        </button>

        <nav id="vestiq-mobile-menu" className={`vestiq-nav-links ${menuOpen ? "open" : ""}`} aria-label="Main navigation">
          <button className={`nav-link ${activeSection === "home" ? "active" : ""}`} onClick={() => scrollTo("home")}>Home</button>
          <button className={`nav-link ${activeSection === "features" ? "active" : ""}`} onClick={() => scrollTo("features")}>Features</button>
          <button className={`nav-link ${activeSection === "how" ? "active" : ""}`} onClick={() => scrollTo("how")}>How it works</button>
          <button className={`nav-link ${activeSection === "about" ? "active" : ""}`} onClick={() => scrollTo("about")}>About</button>
          <button className="enter-nav" onClick={() => { setMenuOpen(false); onEnter(); }}>Enter Vestiq <span>→</span></button>
        </nav>
      </header>

      <div className="vestiq-hero-stage" id="home">
        <section className="vestiq-hero">
          <div className="hero-main-content">
            <p className="eyebrow">YOUR STYLE, SIMPLIFIED.</p>

            <h1>
              Style that
              <em>knows you.</em>
            </h1>

            <p className="hero-copy">
              Vestiq turns the clothes you already own into thoughtful outfits
              for every mood, moment and weather.
            </p>
          </div>

          <button className="hero-cta" onClick={onEnter}>
            Start Your Style Journey <span>→</span>
          </button>

          <button className="secondary-cta" onClick={() => scrollTo("how")}>
            <span className="play">▷</span> See How It Works
          </button>

          <div className="feature-row">
            <article><div className="feature-icon">♧</div><h3>Organize</h3><p>Your world, your way.</p></article>
            <article><div className="feature-icon">♢</div><h3>Style</h3><p>Looks that fit your vibe.</p></article>
            <article><div className="feature-icon">♡</div><h3>Simplify</h3><p>Outfits in seconds.</p></article>
            <article><div className="feature-icon">✧</div><h3>Feel You</h3><p>Confidence, daily.</p></article>
          </div>
        </section>
      </div>

      <section className="vestiq-info-section" id="features">
        <div className="vestiq-info-card features-card">
          <p className="info-eyebrow">VESTIQ FEATURES</p>
          <h2>Everything your wardrobe needs.</h2>
          <p>Vestiq brings the everyday parts of getting dressed together, without changing the clothes or style that already feel like you.</p>
          <div className="how-steps feature-detail-grid">
            <article><span>01</span><h3>Organize</h3><p>Keep your wardrobe pieces together and easy to explore.</p></article>
            <article><span>02</span><h3>Style</h3><p>Discover combinations that fit your personal vibe.</p></article>
            <article><span>03</span><h3>Simplify</h3><p>Make everyday outfit decisions in seconds.</p></article>
            <article><span>04</span><h3>Feel You</h3><p>Build looks that feel comfortable, confident and yours.</p></article>
          </div>
        </div>
      </section>

      <section className="vestiq-info-section" id="how">
        <div className="vestiq-info-card">
          <p className="info-eyebrow">HOW VESTIQ WORKS</p>
          <h2>From wardrobe to outfit, effortlessly.</h2>
          <p>Add the clothes you already own, tell Vestiq what you are dressing for, and get outfit suggestions shaped around your wardrobe, occasion and weather.</p>
          <div className="how-steps">
            <article><span>01</span><h3>Build your wardrobe</h3><p>Add your clothing pieces and keep everything organized in one place.</p></article>
            <article><span>02</span><h3>Tell Vestiq the moment</h3><p>Choose the occasion and let Vestiq consider the day's conditions.</p></article>
            <article><span>03</span><h3>Get your look</h3><p>Explore outfit recommendations made from clothes you already own.</p></article>
          </div>
        </div>
      </section>

      <section className="vestiq-info-section" id="about">
        <div className="vestiq-info-card about-card">
          <p className="info-eyebrow">ABOUT VESTIQ</p>
          <h2>Your wardrobe. Your style. Your Vestiq.</h2>
          <p>Vestiq is designed to make everyday outfit decisions simpler by bringing your wardrobe, personal style, occasion and weather together in one thoughtful experience.</p>
          <button className="info-cta" onClick={onEnter}>Enter Vestiq <span>→</span></button>
        </div>
      </section>

      <a className="github-float" href={GITHUB_URL} target="_blank" rel="noreferrer" aria-label="Open Vestiq GitHub repository">
        <svg viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M12 .7A11.3 11.3 0 0 0 8.43 22.92c.57.1.78-.25.78-.55v-2.16c-3.18.69-3.85-1.34-3.85-1.34-.52-1.32-1.27-1.67-1.27-1.67-1.04-.71.08-.7.08-.7 1.15.08 1.76 1.18 1.76 1.18 1.02 1.75 2.67 1.24 3.32.95.1-.74.4-1.24.72-1.53-2.54-.29-5.2-1.27-5.2-5.65 0-1.25.45-2.27 1.18-3.07-.12-.29-.51-1.45.11-3.02 0 0 .96-.31 3.12 1.17a10.8 10.8 0 0 1 5.68 0c2.16-1.48 3.12-1.17 3.12-1.17.62 1.57.23 2.73.11 3.02.73.8 1.18 1.82 1.18 3.07 0 4.39-2.67 5.35-5.21 5.64.41.36.77 1.08.77 2.18v3.23c0 .3.2.66.79.55A11.3 11.3 0 0 0 12 .7Z"/></svg>
        <span>GitHub</span>
        <small>Open Source ↗</small>
      </a>
    </main>
  );
}
