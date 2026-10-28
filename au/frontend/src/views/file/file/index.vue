<template>
  <div class="app-container agri-business-page">
    <AgriPageHeader
      title="农业多源数据中心"
      eyebrow="AGRICULTURAL DATA CENTER"
      icon="FolderOpened"
      description="统一管理环境监测、无人机遥感、病害图片、田间调查、农事记录和模型结果文件，支持目录归档、检索、上传与下载。"
    />

    <section class="data-overview-grid">
      <article v-for="item in dataAssetTypes" :key="item.name" class="data-asset-card">
        <span>{{ item.name }}</span>
        <strong>{{ item.count }}<small>{{ item.unit }}</small></strong>
        <el-progress :percentage="item.quality" :stroke-width="7" />
      </article>
    </section>

    <section class="collection-grid">
      <article v-for="item in dataSourcePipelines" :key="item.source" class="collection-card">
        <div>
          <strong>{{ item.source }}</strong>
          <span>{{ item.method }} · {{ item.frequency }}</span>
          <p>{{ item.payload }}</p>
        </div>
        <el-tag :type="item.type">{{ item.status }}</el-tag>
      </article>
    </section>

    <div class="breadcrumb" v-if="currentFolderId !== '0'">
      <el-breadcrumb separator="/">
        <el-breadcrumb-item>
          <a @click="goToRoot">农业数据中心</a>
        </el-breadcrumb-item>
        <el-breadcrumb-item v-for="(folder, index) in breadcrumb" :key="folder.id">
          <a v-if="index < breadcrumb.length - 1" @click="goToFolder(folder)">{{ folder.name }}</a>
          <span v-else>{{ folder.name }}</span>
        </el-breadcrumb-item>
      </el-breadcrumb>
    </div>

    <el-form :model="queryParams" ref="queryParams" size="small" :inline="true" @submit.native.prevent>
      <el-form-item label="数据文件名称">
       <el-input 
    placeholder="搜索基地、地块、数据类型或文件名" 
    v-model="searchInputText"
    @keyup.enter="handleSearch"
    clearable
  ></el-input>
      </el-form-item>
      <el-form-item>
        <el-button type="primary" icon="el-icon-search" size="small" @click="handleSearch">搜索</el-button>
        <el-button icon="el-icon-refresh" size="small" @click="handleReset">重置</el-button>
      </el-form-item>
    </el-form>

    <el-row :gutter="10" class="mb8">
      <el-col :span="1.5">
        <el-button
          type="primary"
          plain
          icon="Plus"
          @click="addFolderWithContent"
          v-hasPermi="['file:file:add']"
        >上传数据目录</el-button>
      </el-col>
      <el-col :span="1.5">
        <el-button
          type="success"
          plain
          icon="Edit"
          :disabled="single"
          @click="updateFloder"
          v-hasPermi="['file:file:edit']"
        >修改</el-button>
      </el-col>
      <el-col :span="1.5">
        <el-button
          type="danger"
          plain
          icon="Delete"
          :disabled="multiple"
          @click="delFloder"
          v-hasPermi="['file:file:remove']"
        >删除</el-button>
      </el-col>
      <el-col :span="1.5">
      </el-col>
      <right-toolbar v-model:showSearch="showSearch" @queryTable="getList"></right-toolbar>
    </el-row>
    
    <div style="position: absolute;height: 80%;width: 98%" @click="addFolderShow = false;folderShow = false;clearSelection()"
         @contextmenu.prevent.stop="rightClick($event)">
      <el-card class="drawing_card" v-loading="cardLoading">
    
        <template v-if="folderList.length === 0">
          <el-empty description="暂无农业数据，请创建目录或上传环境、遥感、病害与调查数据" style="height: 600px"></el-empty>
        </template>
        
        <!-- 上传数据目录对话框 -->
        <el-dialog title="上传数据目录" v-model="uploadFolderVisible" width="500px" append-to-body>
          <el-form ref="uploadFolderRef" :model="uploadFolderForm" :rules="uploadFolderRules" label-width="80px">
            <el-form-item label="数据目录名称" prop="name">
              <el-input v-model="uploadFolderForm.name" placeholder="请输入数据目录名称" />
            </el-form-item>
            <el-form-item label="选择本地数据目录" required>
              <input 
                type="file" 
                ref="folderInput"
                webkitdirectory
                multiple
                @change="handleFolderSelect"
                style="margin-top: 8px;"
              />
              <div v-if="selectedFolderFiles.length > 0" style="margin-top: 8px; color: #666;">
                已选择本地数据目录，包含 {{ selectedFolderFiles.length }} 个文件
              </div>
              <div v-else style="margin-top: 8px; color: #909399; font-size: 12px;">
                请选择包含农业数据文件的目录
              </div>
            </el-form-item>
          </el-form>
          <template #footer>
            <div class="dialog-footer">
              <el-button type="primary" @click="submitUploadFolder">确 定</el-button>
              <el-button @click="uploadFolderVisible = false">取 消</el-button>
            </div>
          </template>
        </el-dialog>

        <!-- 创建空数据目录对话框 -->
        <el-dialog title="创建数据目录" v-model="createFolderVisible" width="400px" append-to-body>
          <el-form ref="createFolderRef" :model="createFolderForm" :rules="createFolderRules" label-width="80px">
            <el-form-item label="数据目录名称" prop="name">
              <el-input v-model="createFolderForm.name" placeholder="请输入数据目录名称" />
            </el-form-item>
          </el-form>
          <template #footer>
            <div class="dialog-footer">
              <el-button type="primary" @click="submitCreateFolder">确 定</el-button>
              <el-button @click="createFolderVisible = false">取 消</el-button>
            </div>
          </template>
        </el-dialog>

        <!-- 批量上传进度对话框 -->
        <el-dialog 
          title="上传数据目录" 
          v-model="batchUploadVisible" 
          width="400px"
          :close-on-click-modal="false"
          :show-close="false"
        >
          <div style="text-align: center;">
            <div style="margin-bottom: 20px;">
              <div v-if="batchUploadStatus === 'uploading'">
                <el-progress 
                  :percentage="batchUploadProgress" 
                  :status="batchUploadProgress === 100 ? 'success' : ''"
                />
                <div style="margin-top: 10px; color: #666;">
                  正在上传农业数据... {{ batchUploadProgress }}%
                </div>
              </div>
              <div v-else-if="batchUploadStatus === 'success'" style="color: #67C23A;">
                <i class="el-icon-success" style="font-size: 48px;"></i>
                <div style="margin-top: 10px;">上传完成！</div>
              </div>
              <div v-else-if="batchUploadStatus === 'exception'" style="color: #F56C6C;">
                <i class="el-icon-error" style="font-size: 48px;"></i>
                <div style="margin-top: 10px;">上传失败，请重试</div>
              </div>
            </div>
          </div>
        </el-dialog>

        <!-- 修改名称对话框 -->
        <el-dialog title="修改名称" v-model="renameDialogVisible" width="400px" append-to-body>
          <el-form>
            <el-form-item label="新名称">
              <el-input v-model="renameForm.newName" placeholder="请输入新的名称" />
            </el-form-item>
          </el-form>
          <template #footer>
            <div class="dialog-footer">
              <el-button type="primary" @click="confirmRename">确 定</el-button>
              <el-button @click="renameDialogVisible = false">取 消</el-button>
            </div>
          </template>
        </el-dialog>
        
<!-- 修改数据目录显示部分 -->
<div v-for="(item,index) in folderList" :key="item.id || index">
  <div class="folderContainer">
    <!-- 数据目录类型显示数据目录图标 -->
    <div v-if="item.type == 'dir'" 
         class="folderWrapper" 
         :class="{ 'selected': selectedItems.includes(item.id) }"
         @click="handleItemClick(item, $event)"
         @dblclick="enterFolder(item)"
         @contextmenu.prevent.stop="rightClickFolder(index,item,$event)">
      <div class="folder">
        <div class="front"></div>
        <div class="center"></div>
        <div class="back"></div>
      </div>
      <div class="folderName">
        <span>{{ item.name && item.name.length > 10 ? item.name.substring(0, 8) + '...' : item.name }}</span>
      </div>
      <div class="folderTime">
        <span>{{ formatTime(item.uploadTime) }}</span>
      </div>
    </div>
    <!-- 文件类型显示文件图标 - 只在非农业数据中心下显示 -->
    <div v-else-if="currentFolderId !== '0'" 
         class="folderWrapper" 
         :class="{ 'selected': selectedItems.includes(item.id) }"
         @click="handleItemClick(item, $event)"
         @dblclick="downloadFile(item)"
         @contextmenu.prevent.stop="rightClickFolder(index,item,$event)">
      <img src="@/assets/images/fileImg.png" style="width: 100px;height: 90px;margin-top: -13px"/>
      <div class="folderName">
        <span>{{ item.name && item.name.length > 10 ? item.name.substring(0, 8) + '...' : item.name }}</span>
      </div>
      <div class="folderTime">
        <span>{{ formatTime(item.uploadTime) }}</span>
      </div>
    </div>
  </div>
</div>
      </el-card>
    </div>
  
    <div class="add-folder" :style="addFolderStyle" v-show="addFolderShow">
      <div class="add-folder-1" style="margin-top: 1.5px;margin-bottom: 1.5px">
        <div class="add-folder-2" style="margin-bottom: 5px" @click="createEmptyFolder">
            <i class="el-icon-plus"></i>
          新建数据目录
        </div>
        <div style="border: 2px solid rgba(18,17,42,.07)"></div>
        <div class="add-folder-2" @click="handleAddFileToFolder" style="margin-bottom: 5px">
            <i class="el-icon-upload2"></i>
          上传农业数据
        </div>
        <div style="border: 2px solid rgba(18,17,42,.07)"></div>
        <div class="add-folder-2" @click="forceRefresh" >
            <i class="el-icon-refresh"></i>
          刷 新
        </div>
      </div>
    </div>

    <div class="add-folder-9" :style="folderStyle" v-show="folderShow">
      <div class="add-folder-1" style="margin-top: 1.5px;margin-bottom: 1.5px">
        <!-- 右键菜单 -->
        <div v-if="currentFolder.type === 'dir'" class="add-folder-2" @click="openFolder(currentFolder)">
            <i class="el-icon-folder-opened"></i>
          数据目录详情
        </div>
        <div v-else class="add-folder-2" @click="downloadFile(currentFolder)">
            <i class="el-icon-download"></i>
          下载农业数据
        </div>
        <div style="border: 2px solid rgba(18,17,42,.07)"></div>
        <div class="add-folder-2" @click="updateFloder">
            <i class="el-icon-edit-outline"></i>
          修改名称
        </div>
        <div style="border: 2px solid rgba(18,17,42,.07)"></div>
        <div class="add-folder-6" @click="delFloder">
            <i class="el-icon-delete"></i>
            删 除
        </div>
      </div>
    </div>
    
  <!-- 农业数据文件列表对话框 -->
<el-dialog 
  :title="`农业数据文件列表 - ${currentFolderName}`" 
  v-model="dialogVisible" 
  width="800px"
  destroy-on-close
  @close="handleDialogClose"
>
  <div>
    <el-form style="margin-top: 20px" :model="fileQueryParams" ref="dialogQueryForm" size="small" :inline="true" @submit.native.prevent>
      <el-form-item label="数据文件名称">
        <el-input placeholder="数据文件名称" v-model="fileQueryParams.name"></el-input>
      </el-form-item>
      <el-form-item>
        <el-button type="primary" icon="el-icon-search" size="small" @click="handleDialogSearch">搜索</el-button>
        <el-button icon="el-icon-refresh" size="small" @click="resetDialogQuery">重置</el-button>
      </el-form-item>
    </el-form>
    
    <el-table :data="fileListData" border v-loading="loading">
      <template #empty>
        <el-empty description="该数据目录暂无农业数据文件"></el-empty>
      </template>
      <el-table-column align="center" prop="name" label="数据文件名称"/>
      <el-table-column align="center" prop="size" label="文件大小">
        <template #default="scope">
          <div>{{ formatFileSize(scope.row.size) }}</div>
        </template>
      </el-table-column>
      <el-table-column align="center" prop="type" label="文件类型"/>
      <el-table-column align="center" prop="uploadTime" label="创建时间">
        <template #default="scope">
          <div>{{ formatTime(scope.row.uploadTime) }}</div>
        </template>
      </el-table-column>
      <el-table-column align="center" label="操作" width="200">
        <template #default="scope">
          <el-button type="text" @click="renameFile(scope.row)">修改名称</el-button>
          <el-button type="text" @click="delFileItem(scope.row.id)">删除</el-button>
          <el-button type="text" @click="downloadFile(scope.row)">下载</el-button>
        </template>
      </el-table-column>
    </el-table>
    
    <div class="pagination" v-if="fileTotal > 0">
      <el-pagination
        v-model:current-page="fileQueryParams.pageNum"
        v-model:page-size="fileQueryParams.pageSize"
        :page-sizes="[5, 10, 20, 50]"
        :total="fileTotal"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="handleFileSizeChange"
        @current-change="handleFileCurrentChange"
      />
    </div>
  </div>
</el-dialog>
    <!-- 上传农业数据对话框 -->
    <el-dialog title="上传农业数据" v-model="uploadFileVisible" width="500px" append-to-body>
      <el-form ref="uploadFileRef" :model="uploadFileForm" :rules="uploadFileRules" label-width="80px">
        <el-form-item label="文件名" prop="name">
          <el-input v-model="uploadFileForm.name" placeholder="请输入文件名" />
        </el-form-item>
        <el-form-item label="文件" prop="file">
          <input 
            type="file" 
            ref="fileInput"
            @change="handleFileSelect"
            style="margin-top: 8px;"
          />
          <div v-if="selectedFile" style="margin-top: 8px; color: #666;">
            已选择: {{ selectedFile.name }}
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <div class="dialog-footer">
          <el-button type="primary" @click="submitUploadFile">确 定</el-button>
          <el-button @click="uploadFileVisible = false">取 消</el-button>
        </div>
      </template>
    </el-dialog>
   </div>
</template>

<script setup name="AgricultureDataCenter">
import AgriPageHeader from '@/components/AgriPageHeader'
import { listFile, addFileFile, updateFile,down,delFile,getFile } from "@/api/file/file";
import { getCurrentInstance, ref, reactive, toRefs, computed, onMounted, watch } from 'vue';
import { dataAssetTypes, dataSourcePipelines } from '@/data/agriculture'

const { proxy } = getCurrentInstance();
const selectedFolderFiles = ref([]);
const folderInput = ref(null);
const batchUploadProgress = ref(0);
const batchUploadVisible = ref(false);
const batchUploadStatus = ref('');
const folderCache = ref({});
const currentFolderId = ref('0'); 
const breadcrumb = ref([]); 
const addFolderShow = ref(false);
const dialogVisible = ref(false); 
const loading = ref(false);
const fileTotal = ref(0);
const folderShow = ref(false);
const cardLoading = ref(false);
const folderName = ref(null);
const folderId = ref(null);
const type = ref(null);
const dataIndex = ref(null);
const single = ref(true);
const multiple = ref(true);
const folderList = ref([]);
const selectedFile = ref(null);
const fileInput = ref(null);
const showSearch = ref(true);
const currentFolder = ref({});
const currentFolderName = ref('');
const fileListData = ref([]);
const renameDialogVisible = ref(false);
const uploadFolderVisible = ref(false);
const createFolderVisible = ref(false);
const uploadFileVisible = ref(false);
const uploadingFolderId = ref(null);
const searchText = ref('');
const searchInputText = ref('');
const selectedItems = ref([]);

const renameForm = reactive({
  newName: '',
  item: null,
  type: 'folder' 
});

const uploadFolderForm = reactive({
  name: '',
  folder: null
});

const uploadFolderRules = {
  name: [{ required: true, message: "数据目录名称不能为空", trigger: "blur" }]
};

const createFolderForm = reactive({
  name: ''
});

const createFolderRules = {
  name: [{ required: true, message: "数据目录名称不能为空", trigger: "blur" }]
};

const uploadFileForm = reactive({
  name: '',
  file: null
});

const uploadFileRules = {
  name: [{ required: true, message: "文件名不能为空", trigger: "blur" }],
  file: [{ required: true, message: "请选择文件", trigger: "change" }]
};

const data = reactive({
  props: {
    containerId: {
      type: Number,
      required: true
    }
  },
  addFolderStyle: {
    left: '0px',
    top: '0px'
  },
  folderStyle: {
    left: '0px',
    top: '0px'
  },
  queryParams: {
    pageNum: 1,
    pageSize: 1000, 
    name: null,
    root: '0'
  },
  fileQueryParams: {
    pageNum: 1,
    pageSize: 10,
    name: null,
    root: '1'
  }
});

const { queryParams, addFolderStyle, folderStyle, fileQueryParams } = toRefs(data);
const delay = (ms) => new Promise(resolve => setTimeout(resolve, ms));
const fileDataList = computed(() => {
  const start = (fileQueryParams.value.pageNum - 1) * fileQueryParams.value.pageSize;
  const end = start + fileQueryParams.value.pageSize;
  return fileListData.value.slice(start, end);
});

// 监听选中项变化，更新按钮状态
watch(selectedItems, (newVal) => {
  single.value = newVal.length !== 1;
  multiple.value = newVal.length === 0;
}, { deep: true });

function formatTime(timeStr) {
  if (!timeStr) return '';
  try {
    const date = new Date(timeStr);
    return date.toLocaleString();
  } catch (e) {
    return timeStr;
  }
}
function formatFileSize(bytes) {
  if (!bytes || bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}
function getFileType(filename) {
  const ext = filename.split('.').pop().toLowerCase();
  const typeMap = {
    'jpg': 'image',
    'jpeg': 'image', 
    'png': 'image',
    'gif': 'image',
    'pdf': 'document',
    'doc': 'document',
    'docx': 'document',
    'xls': 'document',
    'xlsx': 'document',
    'txt': 'text',
    'zip': 'archive',
    'rar': 'archive',
    '7z': 'archive'
  };
  return typeMap[ext] || 'file';
}
function handleFileSelect(event) {
  const file = event.target.files[0];
  if (file) {
    selectedFile.value = file;
    uploadFileForm.file = file;
    
    if (!uploadFileForm.name) {
      uploadFileForm.name = file.name;
    }
  }
}
function handleFolderSelect(event) {
  const files = Array.from(event.target.files);
  if (files.length > 0) {
    selectedFolderFiles.value = files;
    if (!uploadFolderForm.name) {
      const firstFile = files[0];
      if (firstFile.webkitRelativePath) {
        const pathParts = firstFile.webkitRelativePath.split('/');
        const folderName = pathParts[0];
        uploadFolderForm.name = folderName;
      }
    }
  }
}

// 处理项目单击事件
function handleItemClick(item, event) {
  event.stopPropagation(); 
  
  // 如果按住Ctrl键，则多选
  if (event.ctrlKey || event.metaKey) {
    const index = selectedItems.value.indexOf(item.id);
    if (index > -1) {

      selectedItems.value.splice(index, 1);
    } else {
  
      selectedItems.value.push(item.id);
    }
  } else {

    selectedItems.value = [item.id];
  }

  currentFolder.value = item;
  folderName.value = item.name;
  folderId.value = item.id;
  type.value = item.type;
  
  console.log('选中项:', selectedItems.value);
}

// 清除选中
function clearSelection() {
  selectedItems.value = [];
  currentFolder.value = {};
}

// 上传有内容的数据目录
function addFolderWithContent() {
  addFolderShow.value = false;
  resetUploadFolderForm();
  uploadFolderVisible.value = true;
}

// 创建空数据目录
function createEmptyFolder() {
  addFolderShow.value = false;
  resetCreateFolderForm();
  createFolderVisible.value = true;
}

// 提交上传数据目录
function submitUploadFolder() {
  proxy.$refs["uploadFolderRef"].validate(valid => {
    if (valid) {
      if (selectedFolderFiles.value.length === 0) {
        proxy.$modal.msgError("请选择要上传的数据目录");
        return;
      }
      uploadFolderWithFiles();
    }
  });
}

// 提交创建空数据目录
function submitCreateFolder() {
  proxy.$refs["createFolderRef"].validate(valid => {
    if (valid) {
      createEmptyFolderApi();
    }
  });
}

// 创建空数据目录
function createEmptyFolderApi() {
  const formData = new FormData();
  const emptyFile = new File([], 'empty.txt', { type: 'text/plain' });
  formData.append('file', emptyFile);
  formData.append('name', createFolderForm.name);
  formData.append('type', 'dir');
  formData.append('root', currentFolderId.value); 
  
  addFileFile(formData).then(response => {
    proxy.$modal.msgSuccess("数据目录创建成功");
    createFolderVisible.value = false;
    
    // 刷新列表
    list();
  }).catch(error => {
    console.error("创建数据目录错误:", error);
    proxy.$modal.msgError("操作失败: " + (error.response?.data?.message || error.message));
  });
}

// 重置上传数据目录表单
function resetUploadFolderForm() {
  uploadFolderForm.name = '';
  uploadFolderForm.folder = null;
  selectedFolderFiles.value = [];
  
  if (folderInput.value) {
    folderInput.value.value = '';
  }
  if (proxy.$refs["uploadFolderRef"]) {
    proxy.$refs["uploadFolderRef"].resetFields();
  }
}

// 重置创建数据目录表单
function resetCreateFolderForm() {
  createFolderForm.name = '';
  if (proxy.$refs["createFolderRef"]) {
    proxy.$refs["createFolderRef"].resetFields();
  }
}

// 重置上传农业数据表单
function resetUploadFileForm() {
  uploadFileForm.name = '';
  uploadFileForm.file = null;
  selectedFile.value = null;
  
  if (fileInput.value) {
    fileInput.value.value = '';
  }
  if (proxy.$refs["uploadFileRef"]) {
    proxy.$refs["uploadFileRef"].resetFields();
  }
}
// 处理输入事件
function handleSearch() {
  queryParams.value.name = searchInputText.value;
  list();
}
function handleReset() {
  searchInputText.value = '';
  queryParams.value.name = '';
  list();
}


// 查询数据目录列表 
async function list() {
  cardLoading.value = true;
  queryParams.value.root = currentFolderId.value;
  
  console.log('查询数据目录参数:', queryParams.value);
  
  const listParams = {
    ...queryParams.value,
    pageNum: 1,
    pageSize: 1000 
  };
  
  try {
    const res = await listFile(listParams);
    console.log('数据目录列表响应:', res);
    
    let data = [];
    if (res.rows) {
      data = res.rows;
    } else if (res.data) {
      data = res.data;
    }

    // 直接使用从接口获取的数据，不再合并任务结果数据目录
    if (currentFolderId.value === '0') {
      // 获取农业数据目录
      const rootFolders = data.filter(item => {
        return (item.root === '0' || item.root === 0 || item.root === null || item.root === undefined) && item.type === 'dir';
      });
      // 同名农业数据只保留一个主目录入口，避免重复平铺显示
      folderList.value = Array.from(
        rootFolders.reduce((folders, item) => {
          const key = (item.name || '').trim().toLowerCase();
          const current = folders.get(key);
          if (!current || Number(item.id) < Number(current.id)) folders.set(key, item);
          return folders;
        }, new Map()).values()
      );
    } else {
      folderList.value = data.filter(item => {
        return String(item.root) === String(currentFolderId.value);
      });
    }
    
    cardLoading.value = false;
  } catch (error) {
    console.error('获取项目列表失败:', error);
    cardLoading.value = false;
  }
  addFolderShow.value = false;
}

// 处理任务结果数据目录
function enterFolder(folder) {
  if (folder.type !== 'dir') {
    return; 
  }
  
  currentFolderId.value = folder.id;
  currentFolder.value = folder;
  updateBreadcrumb(folder);
  list();
  folderShow.value = false;
  clearSelection();
}

function openFolder(folder) {
  if (folder.type !== 'dir') {
    return; 
  }
  
  currentFolder.value = folder;
  currentFolderName.value = folder.name;
  folderShow.value = false;
  
  // 重置查询参数
  fileQueryParams.value = {
    pageNum: 1,
    pageSize: 10,
    name: null,
    root: folder.id
  };
  
  getFileList();
  dialogVisible.value = true;
}


onMounted(() => {
  list();
});

onUnmounted(() => {
});



function updateBreadcrumb(folder) {
  if (folder.id === '0') {
    breadcrumb.value = [];
    return;
  }
  if (!breadcrumb.value.some(item => item.id === folder.id)) {
    breadcrumb.value.push(folder);
  }
}

// 返回农业数据中心
function goToRoot() {
  currentFolderId.value = '0';
  breadcrumb.value = [];
  list();
  clearSelection();
}

// 跳转到指定数据目录
function goToFolder(folder) {
  const index = breadcrumb.value.findIndex(item => item.id === folder.id);
  if (index !== -1) {
    breadcrumb.value = breadcrumb.value.slice(0, index + 1);
  }
  currentFolderId.value = folder.id;
  currentFolder.value = folder;
  list();
  clearSelection();
}

// 获取农业数据文件列表 
function getFileList() {
  loading.value = true;
  
  // 确保传递正确的分页参数
  const params = {
    ...fileQueryParams.value,
    root: currentFolder.value.id || fileQueryParams.value.root
  };
  
  listFile(params).then(response => {
    if (response.code === 200) {
      // 使用后端返回的分页数据
      fileListData.value = response.rows || [];
      fileTotal.value = response.total || 0;
    } else {
      fileListData.value = [];
      fileTotal.value = 0;
      proxy.$modal.msgError("获取农业数据文件列表失败");
    }
    loading.value = false;
  }).catch((error) => {
    console.error('获取农业数据文件列表失败:', error);
    fileListData.value = [];
    fileTotal.value = 0;
    loading.value = false;
    proxy.$modal.msgError("获取农业数据文件列表失败");
  });
}

function handleFileSizeChange(val) {
  fileQueryParams.value.pageSize = val;
  fileQueryParams.value.pageNum = 1; // 重置到第一页
  getFileList(); 
}

function handleFileCurrentChange(val) {
  fileQueryParams.value.pageNum = val;
  getFileList(); 
}
function handleDialogClose() {
  // 重置分页参数
  fileQueryParams.value = {
    pageNum: 1,
    pageSize: 10,
    name: null,
    root: '1'
  };
  fileListData.value = [];
  fileTotal.value = 0;
}
function handleDialogSearch() {
  fileQueryParams.value.pageNum = 1; // 搜索时回到第一页
  getFileList();
}

function resetDialogQuery() {
  fileQueryParams.value = {
    pageNum: 1,
    pageSize: 10,
    name: null,
    root: currentFolder.value.id || fileQueryParams.value.root
  };
  getFileList();
}

function handleAddFileToFolder() {
  addFolderShow.value = false;
  resetUploadFileForm();
  
  if (folderShow.value && currentFolder.value && currentFolder.value.type === 'dir') {
    uploadFileForm.root = currentFolder.value.id;
  } else {
    // 右键在空白处上传，上传到当前数据目录
    uploadFileForm.root = currentFolderId.value;
  }
  
  console.log('上传农业数据到数据目录:', uploadFileForm.root);
  uploadFileVisible.value = true;
}

function submitUploadFile() {
  proxy.$refs["uploadFileRef"].validate(valid => {
    if (valid) {
      if (!selectedFile.value) {
        proxy.$modal.msgError("请选择要上传的文件");
        return;
      }
      uploadSingleFile();
    }
  });
}

// 上传单个文件
function uploadSingleFile() {
  const formData = new FormData();
  formData.append('file', selectedFile.value);
  formData.append('name', uploadFileForm.name);
  formData.append('type', getFileType(selectedFile.value.name));
  formData.append('root', uploadFileForm.root); // 使用正确的 root
  
  console.log('上传农业数据参数:', {
    name: uploadFileForm.name,
    type: getFileType(selectedFile.value.name),
    root: uploadFileForm.root,
    currentFolderId: currentFolderId.value
  });
  
  addFileFile(formData).then(response => {
    console.log('上传响应:', response);
    proxy.$modal.msgSuccess("文件上传成功");
    uploadFileVisible.value = false;
    
    // 刷新对应的列表
    if (dialogVisible.value) {
      getFileList();
    } else {
      // 如果在主界面，刷新主农业数据文件列表
      list();
    }
    
    forceRefresh();
  }).catch(error => {
    console.error("操作错误:", error);
    proxy.$modal.msgError("操作失败: " + (error.response?.data?.message || error.message));
  });
}
// 强制刷新列表
function forceRefresh() {
  // 清空选中状态
  clearSelection();
  list(); 
  // 如果对话框打开，也刷新对话框列表
  if (dialogVisible.value) {
    getFileList();
  }
  
  console.log('强制刷新完成，当前数据目录ID:', currentFolderId.value);
}
// 上传包含文件的数据目录 
async function uploadFolderWithFiles() {
  batchUploadProgress.value = 0;
  batchUploadVisible.value = true;
  batchUploadStatus.value = 'uploading';

  try {
    // 同名主目录存在时直接复用，目录内继续按本地层级创建子目录和文件
    const folderId = await ensureFolderExists(currentFolderId.value, uploadFolderForm.name.trim());
    uploadingFolderId.value = folderId;
    await uploadFolderRecursively(folderId);
  } catch (error) {
    console.error("创建数据目录错误:", error);
    batchUploadStatus.value = 'exception';
    proxy.$modal.msgError(error.response?.data?.message || error.message || '创建数据目录失败');
  }
}

// 递归上传数据目录及其内容
async function uploadFolderRecursively(parentFolderId) {
  const files = selectedFolderFiles.value;
  const totalFiles = files.length;
  let uploadedCount = 0;
  const folderStructure = buildFolderStructure(files);
  try {
    await processFolderStructure(parentFolderId, folderStructure, (progress) => {
      uploadedCount = progress.uploadedCount;
      batchUploadProgress.value = Math.round((uploadedCount / totalFiles) * 100);
    });
    batchUploadProgress.value = 100;
    batchUploadStatus.value = 'success';
    proxy.$modal.msgSuccess(`数据目录上传完成，共上传 ${uploadedCount} 个文件`);
    
    setTimeout(() => {
      batchUploadVisible.value = false;
      uploadFolderVisible.value = false;
      uploadingFolderId.value = null; 
      list();
    }, 1000);
    
  } catch (error) {
    console.error('递归上传失败:', error);
    batchUploadStatus.value = 'exception';
    uploadingFolderId.value = null; 
    proxy.$modal.msgError("数据目录上传失败: " + error.message);
  }
}

// 构建数据目录结构
function buildFolderStructure(files) {
  const structure = {
    files: [],
    folders: {}
  };
  
  files.forEach(file => {
    if (file.webkitRelativePath) {
      const pathParts = file.webkitRelativePath.split('/');
      let currentLevel = structure;

      for (let i = 1; i < pathParts.length - 1; i++) {
        const folderName = pathParts[i];
        if (!currentLevel.folders[folderName]) {
          currentLevel.folders[folderName] = {
            files: [],
            folders: {}
          };
        }
        currentLevel = currentLevel.folders[folderName];
      }
  
      currentLevel.files.push(file);
    } else {

      structure.files.push(file);
    }
  });
  
  return structure;
}

// 递归处理数据目录结构
async function processFolderStructure(parentId, structure, progressCallback) {
  let uploadedCount = 0;
  
  for (const file of structure.files) {
    try {
      await uploadFileToFolder(parentId, file);
      uploadedCount++;
      progressCallback({ uploadedCount });

      await delay(500); 
    } catch (error) {
      console.error(`文件 ${file.name} 上传失败:`, error);
      uploadedCount++;
      progressCallback({ uploadedCount });
    }
  }
  
  // 递归处理子数据目录
  for (const [folderName, subStructure] of Object.entries(structure.folders)) {
    try {
      const folderId = await ensureFolderExists(parentId, folderName);
      await processFolderStructure(folderId, subStructure, progressCallback);
    } catch (error) {
      console.error(`创建数据目录 ${folderName} 失败:`, error);
    }
  }
}

async function ensureFolderExists(parentId, folderName) {
  const cacheKey = `${parentId}-${folderName}`;
 
  if (folderCache.value[cacheKey]) {
    return folderCache.value[cacheKey];
  }

  const existingFolderId = await queryFolderIdByName(folderName, parentId);
  if (existingFolderId) {
    folderCache.value[cacheKey] = existingFolderId;
    return existingFolderId;
  }

  await delay(300);
  
  // 创建新数据目录
  const folderFormData = new FormData();
  const emptyFile = new File([], 'empty.txt', { type: 'text/plain' });
  folderFormData.append('file', emptyFile);
  folderFormData.append('name', folderName);
  folderFormData.append('type', 'dir');
  folderFormData.append('root', parentId);
  
  try {
    await addFileFile(folderFormData);

    await delay(500);

    const newFolderId = await queryFolderIdByNameWithRetry(folderName, parentId);
    folderCache.value[cacheKey] = newFolderId;
    
    return newFolderId;
  } catch (error) {
    console.error(`创建数据目录 ${folderName} 失败:`, error);
    throw error;
  }
}

// 上传农业数据到指定数据目录 
async function uploadFileToFolder(folderId, file) {
  const formData = new FormData();
  formData.append('file', file);

  let fileName = file.name;
  if (file.webkitRelativePath) {
 
    const pathParts = file.webkitRelativePath.split('/');
    fileName = pathParts[pathParts.length - 1];
  }
  
  formData.append('name', fileName);
  formData.append('type', getFileType(file.name));
  formData.append('root', folderId);
  
  console.log(`上传农业数据到数据目录 ${folderId}:`, fileName);
  
  try {
    await addFileFile(formData);
 
    await delay(300);
  } catch (error) {
    console.error(`文件 ${fileName} 上传失败:`, error);
    throw error;
  }
}

// 根据数据目录名称和父数据目录ID查询数据目录ID
function queryFolderIdByName(folderName, parentId) {
  return new Promise((resolve, reject) => {
    const queryParams = {
      name: folderName,
      type: 'dir',
      pageNum: 1,
      pageSize: 100
    };
   
    queryParams.root = parentId ?? '0';
    listFile(queryParams).then(response => {
      let data = [];
      if (response.rows) {
        data = response.rows;
      } else if (response.data) {
        data = response.data;
      }
      const matchingFolders = data.filter(item => 
        item.type === 'dir' && 
        item.name === folderName &&
        String(item.root ?? '0') === String(parentId ?? '0')
      );
 
      if (matchingFolders.length > 0) {
        const canonicalFolder = matchingFolders.reduce((prev, current) => {
          return Number(prev.id) < Number(current.id) ? prev : current;
        });
        resolve(canonicalFolder.id);
      } else {
        resolve(null);
      }
    }).catch(error => {
      console.error('查询数据目录失败:', error);
      reject(error);
    });
  });
}

// 带重试的数据目录查询
function queryFolderIdByNameWithRetry(folderName, parentId, maxRetries = 5, delay = 1000) {
  return new Promise((resolve, reject) => {
    const tryQuery = (attempt) => {
      queryFolderIdByName(folderName, parentId)
        .then(folderId => {
          if (folderId) {
            resolve(folderId);
          } else if (attempt < maxRetries) {
            console.log(`第 ${attempt} 次查询数据目录失败，${delay}ms后重试...`);
            setTimeout(() => tryQuery(attempt + 1), delay);
          } else {
            reject(new Error(`重试 ${maxRetries} 次后仍未找到数据目录 ${folderName}`));
          }
        })
        .catch(error => {
          if (attempt < maxRetries) {
            console.log(`第 ${attempt} 次查询数据目录失败，${delay}ms后重试...`);
            setTimeout(() => tryQuery(attempt + 1), delay);
          } else {
            reject(error);
          }
        });
    };
    
    tryQuery(1);
  });
}

// 修改名称数据目录
function updateFloder() {
  folderShow.value = false;
  if (selectedItems.value.length === 0) {
    proxy.$modal.msgError("请先选择一个项目");
    return;
  }
  
  const selectedItem = folderList.value.find(item => item.id === selectedItems.value[0]);
  if (!selectedItem) {
    proxy.$modal.msgError("选中的项目不存在");
    return;
  }
  
  renameForm.newName = selectedItem.name;
  renameForm.item = selectedItem;
  renameForm.type = selectedItem.type === 'dir' ? 'folder' : 'file';
  renameDialogVisible.value = true;
}

// 确认修改名称
function confirmRename() {
  if (!renameForm.newName) {
    proxy.$modal.msgError("请输入新名称");
    return;
  }

  const updateData = {
    id: renameForm.item.id,
    name: renameForm.newName,
    type: renameForm.item.type,
    root: renameForm.item.root || currentFolderId.value,
    size: renameForm.item.size || 0,
    uploadTime: renameForm.item.uploadTime || new Date().toISOString()
  };
  if (renameForm.item.type !== 'dir') {
    updateData.filePath = renameForm.item.filePath || '';
    updateData.fileType = renameForm.item.fileType || getFileType(renameForm.item.name);
  }

  updateFile(updateData).then(res => {
    if (res.code == 200) {
      proxy.$modal.msgSuccess("修改名称成功!");
      renameDialogVisible.value = false;
  
      if (renameForm.type === 'folder') {
        list(); 
      } else {
        getFileList();
      }
    } else {
      proxy.$modal.msgError("修改名称失败请重试!");
    }
  }).catch(error => {
    console.error('修改名称错误:', error);
    proxy.$modal.msgError("修改名称失败: " + (error.message || '未知错误'));
  });
}


// 删除数据目录
function delFloder(id) {
  folderShow.value = false;
  let itemsToDelete = [];
  if (selectedItems.value.length > 0) {
    itemsToDelete = folderList.value.filter(item => selectedItems.value.includes(item.id));
  } else if (currentFolder.value && currentFolder.value.id) {
    itemsToDelete = [currentFolder.value];
  } else {
    proxy.$message({
      type: 'error',
      message: '请先选择要删除的项目!'
    });
    return;
  }
  if (itemsToDelete.length === 0) {
    proxy.$message({
      type: 'error',
      message: '没有找到要删除的项目!'
    });
    return;
  }

  proxy.$confirm(`此操作将永久删除选中的 ${itemsToDelete.length} 个项目, 是否继续?`, '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(() => {
    const deletePromises = itemsToDelete.map(item => {
      const itemIdToDelete = Number(item.id);
      console.log('删除项目ID:', itemIdToDelete, '名称:', item.name);

      if (isNaN(itemIdToDelete) || itemIdToDelete <= 0) {
        return Promise.reject(new Error(`无效的项目ID: ${item.id}`));
      }
      
      return delFile(itemIdToDelete).then(res => {
        if (res.code == 200) {
          return { success: true, name: item.name };
        } else {
          return { success: false, name: item.name, error: res.msg };
        }
      }).catch(error => {
        console.error('删除项目错误:', error);
        return { success: false, name: item.name, error: error.message };
      });
    });

    Promise.all(deletePromises).then(results => {
      const successCount = results.filter(r => r.success).length;
      const errorCount = results.filter(r => !r.success).length;

      if (errorCount === 0) {
        proxy.$message({
          type: 'success',
          message: `成功删除 ${successCount} 个项目!`
        });
      } else {
        const errorNames = results.filter(r => !r.success).map(r => r.name).join(', ');
        proxy.$message({
          type: 'error',
          message: `成功删除 ${successCount} 个项目，失败 ${errorCount} 个! 失败的项目: ${errorNames}`
        });
      }
      list();
      clearSelection();
      if (dialogVisible.value && itemsToDelete.some(item => item.id === fileQueryParams.value.root)) {
        dialogVisible.value = false;
      }
    });

  });
}
/** 下载农业数据 */
async function downloadFile(file) {
  try {
    if (!file || !file.id) {
      proxy.$modal.msgError("无法获取文件信息");
      return;
    }

    console.log('下载农业数据:', file.name, 'ID:', file.id);

    const loading = proxy.$loading({
      lock: true,
      text: `正在下载: ${file.name}`,
      background: 'rgba(0, 0, 0, 0.7)'
    });

    const blobData = await down(file.id);
    if (!blobData || blobData.size === 0) {
      throw new Error('文件内容为空');
    }
    const url = window.URL.createObjectURL(blobData);
    const a = document.createElement('a');
    a.href = url;
    a.download = file.name;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
    
    proxy.$modal.msgSuccess(`下载完成: ${file.name}`);
    
  } catch (error) {
    console.error('下载失败:', error);
    proxy.$modal.msgError(`下载失败: ${error.message}`);
  } finally {
    proxy.$loading().close();
  }
}
// 删除文件
function delFileItem(id) {
  proxy.$confirm('此操作将永久删除该文件, 是否继续?', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(() => {
    delFile(id).then(res => {
      if (res.code == 200) {
        proxy.$message({
          type: 'success',
          message: '删除成功!'
        });
        getFileList(); 
      } else {
        proxy.$message({
          type: 'error',
          message: '删除失败请重试!'
        });
      }
    }).catch(error => {
      proxy.$message({
        type: 'error',
        message: '删除失败: ' + (error.message || '未知错误')
      });
    });
  }).catch(() => {
  });
}


// 数据目录右键
function rightClickFolder(index, item, e) {
  if (!selectedItems.value.includes(item.id)) {
    selectedItems.value = [item.id];
  }
  
  currentFolder.value = item;
  folderName.value = item.name;
  folderId.value = item.id;
  type.value = item.type;
  dataIndex.value = index;
  folderStyle.value.left = e.pageX + 'px';
  folderStyle.value.top = e.pageY + 'px';
  folderShow.value = true;
  addFolderShow.value = false;
  
  console.log('右键数据目录:', item.name, 'ID:', item.id, '类型:', item.type);
}
function rightClick(e) {
  addFolderStyle.value.left = e.pageX + 'px';
  addFolderStyle.value.top = e.pageY + 'px';
  addFolderShow.value = true;
  folderShow.value = false;
  
  // 清除之前的数据目录选中状态
  currentFolder.value = {};
  console.log('右键空白处，当前数据目录ID:', currentFolderId.value);
}

// 初始化
onMounted(() => {
  list();
});
</script>
<style scoped>
@import "@/assets/css/file_icon.css";

.data-overview-grid {
  display: grid;
  grid-template-columns: repeat(6, minmax(0, 1fr));
  gap: 12px;
  margin-bottom: 14px;
}

.data-asset-card {
  min-width: 0;
  padding: 15px;
  border: 1px solid #dfeae2;
  border-radius: 12px;
  background: linear-gradient(145deg, #ffffff 0%, #f2fbf5 100%);
  box-shadow: 0 8px 22px rgba(19, 108, 56, 0.07);
}

.data-asset-card span,
.data-asset-card strong {
  display: block;
}

.data-asset-card span {
  overflow: hidden;
  color: #728079;
  font-size: 12px;
  white-space: nowrap;
  text-overflow: ellipsis;
}

.data-asset-card strong {
  margin: 6px 0 8px;
  color: #223e2c;
  font-size: 24px;
}

.data-asset-card small {
  margin-left: 4px;
  color: #849088;
  font-size: 12px;
  font-weight: 500;
}

.collection-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
  margin-bottom: 16px;
}

.collection-card {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  min-width: 0;
  padding: 14px 15px;
  border: 1px solid #dfeae2;
  border-radius: 12px;
  background: linear-gradient(145deg, #ffffff 0%, #f1faf4 100%);
  box-shadow: 0 8px 22px rgba(19, 108, 56, 0.07);
}

.collection-card div {
  min-width: 0;
}

.collection-card strong,
.collection-card span {
  display: block;
}

.collection-card strong {
  color: #24422e;
  font-size: 14px;
}

.collection-card span {
  margin-top: 5px;
  color: #2f7c45;
  font-size: 12px;
}

.collection-card p {
  margin: 7px 0 0;
  overflow: hidden;
  color: #6f7c73;
  font-size: 12px;
  line-height: 1.5;
  white-space: nowrap;
  text-overflow: ellipsis;
}

.breadcrumb {
  margin-bottom: 15px;
  padding: 10px;
  border: 1px solid #cfe8d7;
  background: #f2faf4;
  border-radius: 4px;
}

.breadcrumb a {
  cursor: pointer;
  color: #168447;
}

.breadcrumb a:hover {
  color: #0b6b38;
}

.folderContainer {
  display: inline-block;
  margin: 10px;
  text-align: center;
}

.folderWrapper {
  cursor: pointer;
  padding: 10px;
  border-radius: 5px;
  transition: all 0.3s;
  border: 2px solid transparent;
}

.folderWrapper:hover {
  background-color: rgba(38, 153, 82, 0.09);
}

.folderWrapper.selected {
  background-color: rgba(38, 153, 82, 0.16);
  border-color: rgba(38, 153, 82, 0.28);
  width:140px;
  height:100px;
}

.folderName {
  margin-top: 5px;
  font-size: 14px;
  color: #155f36;
  font-weight: 600;
}

.folderTime {
  margin-top: 2px;
  font-size: 12px;
  color: #909399;
}

.pagination {
  margin-top: 15px;
  text-align: right;
}




.agri-business-page {
  min-height: calc(100vh - 84px);
  background: linear-gradient(180deg, #eff9f2 0%, #e2f3e7 100%) !important;
}

.drawing_card {
  border: 1px solid #c9e5d2 !important;
  background:
    radial-gradient(circle at 90% 10%, rgba(72, 179, 104, 0.10), transparent 30%),
    linear-gradient(145deg, #f8fdf9 0%, #e9f7ed 100%) !important;
  box-shadow: 0 12px 30px rgba(16, 91, 46, 0.10) !important;
}

.drawing_card :deep(.el-card__body) {
  min-height: 620px;
  background: transparent !important;
}

.drawing_card :deep(.el-empty__description) {
  color: #6f8376 !important;
}

@media (max-width: 1400px) {
  .data-overview-grid { grid-template-columns: repeat(3, minmax(0, 1fr)); }
  .collection-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
}

@media (max-width: 760px) {
  .data-overview-grid,
  .collection-grid { grid-template-columns: 1fr; }
}
</style>
