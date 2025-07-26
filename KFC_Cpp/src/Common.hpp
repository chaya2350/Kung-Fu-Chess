#pragma once

#include <utility>
#include <cstddef>
#include <memory>
namespace std {
    // Minimal stand-in for std::optional for environments where it is missing
    struct nullopt_t { explicit constexpr nullopt_t(int) {} };
    constexpr nullopt_t nullopt{0};

    template<typename T>
    class optional {
        bool has_{false};
        T value_{};
    public:
        optional() = default;
        optional(nullopt_t) : has_(false) {}
        optional(const T& v) : has_(true), value_(v) {}
        bool has_value() const { return has_; }
        explicit operator bool() const { return has_; }
        T& value() { return value_; }
        const T& value() const { return value_; }
        T value_or(const T& default_val) const { return has_ ? value_ : default_val; }
    };
}

struct PairHash {
    size_t operator()(const std::pair<int,int>& p) const noexcept {
        return static_cast<size_t>(p.first) * 31u + static_cast<size_t>(p.second);
    }
}; 