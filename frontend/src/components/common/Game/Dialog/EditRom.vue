<script setup lang="ts">
import GameCard from "@/components/common/Game/Card/Base.vue";
import RDialog from "@/components/common/RDialog.vue";
import romApi, { type UpdateRom } from "@/services/api/rom";
import storeHeartbeat from "@/stores/heartbeat";
import storeRoms, { type SimpleRom } from "@/stores/roms";
import type { Events } from "@/types/emitter";
import type { Emitter } from "mitt";
import { inject, ref, computed } from "vue";
import { useRoute } from "vue-router";
import { useDisplay, useTheme } from "vuetify";

// Props
const theme = useTheme();
const { lgAndUp, mdAndUp, smAndUp, smAndDown } = useDisplay();
const heartbeat = storeHeartbeat();
const route = useRoute();
const show = ref(false);
const rom = ref<UpdateRom>();
const romsStore = storeRoms();
const imagePreviewUrl = ref<string | undefined>("");
const removeCover = ref(false);
const emitter = inject<Emitter<Events>>("emitter");
emitter?.on("showEditRomDialog", (romToEdit: UpdateRom | undefined) => {
  show.value = true;
  rom.value = romToEdit;
  removeCover.value = false;
});
emitter?.on("updateUrlCover", (url_cover) => {
  if (!rom.value) return;
  rom.value.url_cover = url_cover;
  setArtwork(url_cover);
});

// Functions
function triggerFileInput() {
  const fileInput = document.getElementById("file-input");
  fileInput?.click();
}

function previewImage(event: Event) {
  const input = event.target as HTMLInputElement;
  if (!input.files) return;

  const reader = new FileReader();
  reader.onload = () => {
    setArtwork(reader.result?.toString() || "");
  };
  if (input.files[0]) {
    reader.readAsDataURL(input.files[0]);
  }
}

function setArtwork(imageUrl: string) {
  if (!imageUrl) return;
  imagePreviewUrl.value = imageUrl;
  removeCover.value = false;
}

async function removeArtwork() {
  imagePreviewUrl.value = `/assets/default/cover/big_${theme.global.name.value}_missing_cover.png`;
  removeCover.value = true;
}

const noMetadataMatch = computed(() => {
  return !rom.value?.igdb_id && !rom.value?.moby_id && !rom.value?.sgdb_id;
});

async function handleRomUpdate(
  options: {
    rom: UpdateRom;
    renameAsSource?: boolean;
    removeCover?: boolean;
    unmatch?: boolean;
  },
  successMessage: string,
) {
  show.value = false;
  emitter?.emit("showLoadingDialog", { loading: true, scrim: true });

  await romApi
    .updateRom(options)
    .then(({ data }) => {
      emitter?.emit("snackbarShow", {
        msg: successMessage,
        icon: "mdi-check-bold",
        color: "green",
      });
      romsStore.update(data as SimpleRom);
      if (route.name == "rom") {
        romsStore.currentRom = data;
      }
    })
    .catch((error) => {
      console.log(error);
      emitter?.emit("snackbarShow", {
        msg: error.response.data.detail,
        icon: "mdi-close-circle",
        color: "red",
      });
    })
    .finally(() => {
      emitter?.emit("showLoadingDialog", { loading: false, scrim: false });
      closeDialog();
    });
}

async function unmatchRom() {
  if (!rom.value) return;
  await handleRomUpdate(
    { rom: rom.value, unmatch: true },
    "Rom unmatched successfully",
  );
}

async function updateRom() {
  if (!rom.value?.file_name) {
    emitter?.emit("snackbarShow", {
      msg: "Cannot save: file name is required",
      icon: "mdi-close-circle",
      color: "red",
    });
    return;
  }

  await handleRomUpdate(
    { rom: rom.value, removeCover: removeCover.value },
    "Rom updated successfully!",
  );
}

function closeDialog() {
  show.value = false;
  imagePreviewUrl.value = "";
  rom.value = undefined;
}
</script>

<template>
  <r-dialog
    v-if="rom"
    @close="closeDialog"
    v-model="show"
    icon="mdi-pencil-box"
    scroll-content
    :width="lgAndUp ? '65vw' : '95vw'"
  >
    <template #content>
      <v-row class="align-center pa-2" no-gutters>
        <v-col cols="12" md="8" lg="8" xl="9">
          <v-row class="px-2" no-gutters>
            <v-col>
              <v-text-field
                v-model="rom.name"
                class="py-2"
                label="Name"
                variant="outlined"
                required
                hide-details
                @keyup.enter="updateRom()"
              />
            </v-col>
          </v-row>
          <v-row class="px-2" no-gutters>
            <v-col>
              <v-text-field
                v-model="rom.file_name"
                class="py-2"
                :rules="[(value: string) => !!value]"
                label="Filename"
                variant="outlined"
                required
                hide-details
                @keyup.enter="updateRom()"
              >
                <v-label
                  v-if="smAndUp"
                  id="file-name-label"
                  class="text-caption"
                >
                  <v-icon size="small" class="mr-1">
                    mdi-folder-file-outline
                  </v-icon>
                  <span>
                    /romm/library/{{ rom.file_path }}/{{ rom.file_name }}
                  </span>
                </v-label>
              </v-text-field>
            </v-col>
          </v-row>
          <v-row class="px-2" no-gutters>
            <v-col>
              <v-textarea
                v-model="rom.summary"
                class="py-2"
                label="Summary"
                variant="outlined"
                required
                hide-details
                @keyup.enter="updateRom"
              />
            </v-col>
          </v-row>
          <v-row
            v-if="mdAndUp"
            class="justify-space-between mt-4 mb-2 mx-2"
            no-gutters
          >
            <v-btn-group divided density="compact">
              <v-btn
                :disabled="noMetadataMatch"
                :class="` ${
                  noMetadataMatch ? '' : 'bg-terciary text-romm-red'
                }`"
                variant="flat"
                @click="unmatchRom"
              >
                Unmatch Rom
              </v-btn>
            </v-btn-group>
            <v-btn-group divided density="compact">
              <v-btn class="bg-terciary" @click="closeDialog"> Cancel </v-btn>
              <v-btn class="text-romm-green bg-terciary" @click="updateRom">
                Save
              </v-btn>
            </v-btn-group>
          </v-row>
        </v-col>
        <v-col>
          <v-row class="justify-center">
            <v-col :class="{ 'mobile-cover': smAndDown, 'pa-8': !smAndDown }">
              <game-card :rom="rom" :src="imagePreviewUrl">
                <template #append-inner-right>
                  <v-btn-group rounded="0" divided density="compact">
                    <v-btn
                      :disabled="
                        !heartbeat.value.METADATA_SOURCES?.STEAMGRIDDB_ENABLED
                      "
                      size="small"
                      class="translucent-dark"
                      @click="
                        emitter?.emit(
                          'showSearchCoverDialog',
                          rom?.name as string,
                        )
                      "
                    >
                      <v-icon size="large">mdi-image-search-outline</v-icon>
                    </v-btn>
                    <v-btn
                      size="small"
                      class="translucent-dark"
                      @click="triggerFileInput"
                    >
                      <v-icon size="large">mdi-pencil</v-icon>
                      <v-file-input
                        id="file-input"
                        v-model="rom.artwork"
                        accept="image/*"
                        hide-details
                        class="file-input"
                        @change="previewImage"
                      />
                    </v-btn>
                    <v-btn
                      size="small"
                      class="translucent-dark"
                      @click="removeArtwork"
                    >
                      <v-icon size="large" class="text-romm-red"
                        >mdi-delete</v-icon
                      >
                    </v-btn>
                  </v-btn-group>
                </template>
              </game-card>
            </v-col>
          </v-row>
          <v-row v-if="smAndDown" class="justify-space-between pa-4">
            <v-btn-group divided density="compact" class="my-1">
              <v-btn
                :disabled="noMetadataMatch"
                :class="` ${
                  noMetadataMatch ? '' : 'bg-terciary text-romm-red'
                }`"
                variant="flat"
                @click="unmatchRom"
              >
                Unmatch Rom
              </v-btn>
            </v-btn-group>
            <v-btn-group divided density="compact" class="my-1">
              <v-btn class="bg-terciary" @click="closeDialog"> Cancel </v-btn>
              <v-btn class="text-romm-green bg-terciary" @click="updateRom">
                Save
              </v-btn>
            </v-btn-group>
          </v-row>
        </v-col>
      </v-row>
    </template>
  </r-dialog>
</template>
<style scoped>
.mobile-cover {
  min-width: 240px;
  min-height: 330px;
  max-width: 240px;
  max-height: 330px;
}
</style>

<style>
#file-name-label {
  position: absolute;
  right: 1rem;
}
</style>
