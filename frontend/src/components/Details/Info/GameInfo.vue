<script setup lang="ts">
import storeGalleryFilter, { type FilterType } from "@/stores/galleryFilter";
import type { DetailedRom } from "@/stores/roms";
import { ref } from "vue";
import { useDisplay } from "vuetify";
import { useRouter } from "vue-router";

const props = defineProps<{ rom: DetailedRom }>();
const { xs } = useDisplay();
const show = ref(false);
const carousel = ref(0);
const router = useRouter();
const filters = ["genres", "franchises", "collections", "companies"] as const;

function onFilterClick(filter: FilterType, value: string) {
  router.push({
    name: "platform",
    params: { platform: props.rom.platform_id },
    query: { filter, value },
  });
}
</script>
<template>
  <v-row no-gutters>
    <v-col>
      <v-divider class="mx-2 my-4" />
      <template v-for="filter in filters" :key="filter">
        <v-row
          v-if="rom[filter].length > 0"
          class="align-center my-3"
          no-gutters
        >
          <v-col cols="3" xl="2" class="text-capitalize">
            <span>{{ filter }}</span>
          </v-col>
          <v-col>
            <v-chip
              v-for="value in rom[filter]"
              :key="value"
              @click="onFilterClick(filter, value)"
              size="small"
              variant="outlined"
              class="my-1 mr-2"
              label
            >
              {{ value }}
            </v-chip>
          </v-col>
        </v-row>
      </template>
      <!-- Manually add age ratings to display logos -->
      <template
        v-if="
          rom.igdb_metadata?.age_ratings &&
          rom.igdb_metadata.age_ratings.length > 0
        "
      >
        <v-row no-gutters class="mt-5">
          <v-col cols="3" xl="2" class="text-capitalize">
            <span>Age Rating</span>
          </v-col>
          <div class="d-flex">
            <v-img
              v-for="value in rom.igdb_metadata.age_ratings"
              :key="value.rating"
              @click="onFilterClick('age_ratings', value.rating)"
              :src="value.rating_cover_url"
              height="50"
              width="50"
              class="mr-4 cursor-pointer"
            />
          </div>
        </v-row>
      </template>
      <template v-if="rom.summary != ''">
        <v-divider class="mx-2 my-4" />
        <v-row no-gutters>
          <v-col class="text-caption">
            <span>{{ rom.summary }}</span>
          </v-col>
        </v-row>
      </template>
      <template
        v-if="rom.merged_screenshots.length > 0 || rom.youtube_video_id"
      >
        <v-divider class="mx-2 my-4" />
        <v-row no-gutters>
          <v-col>
            <v-carousel
              v-model="carousel"
              hide-delimiter-background
              delimiter-icon="mdi-square"
              class="bg-primary"
              show-arrows="hover"
              hide-delimiters
              progress="terciary"
              :height="xs ? '300' : '400'"
            >
              <template #prev="{ props }">
                <v-btn
                  icon="mdi-chevron-left"
                  class="translucent-dark"
                  @click="props.onClick"
                />
              </template>
              <v-carousel-item
                v-if="rom.youtube_video_id"
                :key="rom.youtube_video_id"
                content-class="d-flex justify-center align-center"
              >
                <iframe
                  height="100%"
                  :src="`https://www.youtube.com/embed/${rom.youtube_video_id}`"
                  title="YouTube video player"
                  frameborder="0"
                  allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
                  referrerpolicy="strict-origin-when-cross-origin"
                  style="aspect-ratio: 16 / 9"
                  allowfullscreen
                ></iframe>
              </v-carousel-item>
              <v-carousel-item
                v-for="screenshot_url in rom.merged_screenshots"
                :key="screenshot_url"
                :src="screenshot_url"
                class="pointer"
                @click="show = true"
              >
              </v-carousel-item>
              <template #next="{ props }">
                <v-btn
                  icon="mdi-chevron-right"
                  class="translucent-dark"
                  @click="props.onClick"
                />
              </template>
            </v-carousel>
            <v-dialog v-model="show">
              <v-list-item>
                <template #append>
                  <v-btn @click="show = false" icon variant="flat" size="large"
                    ><v-icon class="text-white text-shadow" size="25"
                      >mdi-close</v-icon
                    ></v-btn
                  >
                </template>
              </v-list-item>
              <v-carousel
                v-model="carousel"
                hide-delimiter-background
                delimiter-icon="mdi-square"
                show-arrows="hover"
                hide-delimiters
                :height="xs ? '500' : '600'"
              >
                <template #prev="{ props }">
                  <v-btn
                    @click="props.onClick"
                    icon="mdi-chevron-left"
                    class="translucent-dark"
                  />
                </template>
                <v-carousel-item
                  v-if="rom.youtube_video_id"
                  :key="rom.youtube_video_id"
                  content-class="d-flex justify-center align-center"
                >
                  <iframe
                    height="100%"
                    :src="`https://www.youtube.com/embed/${rom.youtube_video_id}`"
                    title="YouTube video player"
                    frameborder="0"
                    allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
                    referrerpolicy="strict-origin-when-cross-origin"
                    style="aspect-ratio: 16 / 9"
                    allowfullscreen
                  ></iframe>
                </v-carousel-item>
                <v-carousel-item
                  v-for="screenshot_url in rom.merged_screenshots"
                  :key="screenshot_url"
                  :src="screenshot_url"
                >
                </v-carousel-item>
                <template #next="{ props }">
                  <v-btn
                    icon="mdi-chevron-right"
                    class="translucent-dark"
                    @click="props.onClick"
                  />
                </template>
              </v-carousel>
            </v-dialog>
          </v-col>
        </v-row> </template></v-col
  ></v-row>
</template>
