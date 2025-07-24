#include <doctest/doctest.h>
#include <nlohmann/json.hpp>
#include <fstream>
#include <filesystem>

TEST_CASE("NW piece need_clear_path flag") {
    namespace fs = std::filesystem;
    fs::path cfg = fs::path("..") / "KungFu Chess" / "pieces" / "NW" / "states" / "idle" / "config.json";
    std::ifstream in(cfg);
    REQUIRE_MESSAGE(in, "config.json must exist");
    nlohmann::json j; in >> j;
    CHECK(j["physics"].contains("need_clear_path"));
    CHECK(j["physics"]["need_clear_path"].get<bool>() == false);
} 